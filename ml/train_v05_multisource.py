#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score, average_precision_score, balanced_accuracy_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import FeatureUnion, Pipeline

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from ml.v02_text import canonical_template, normalize_model_text, short_hash

THRESHOLDS = [0.50, 0.60, 0.70, 0.80, 0.90]


def word_char(class_weight):
    return Pipeline([
        ('features', FeatureUnion([
            ('word', TfidfVectorizer(lowercase=True, strip_accents='unicode', ngram_range=(1,2), min_df=2, max_df=0.995, sublinear_tf=True, max_features=110_000)),
            ('char', TfidfVectorizer(analyzer='char_wb', lowercase=True, ngram_range=(3,5), min_df=2, sublinear_tf=True, max_features=180_000)),
        ])),
        ('clf', LogisticRegression(class_weight=class_weight, max_iter=5000, random_state=42, solver='liblinear')),
    ])


def candidates():
    return {
        'word_char_balanced_v05': word_char('balanced'),
        'word_char_neg2_v05': word_char({0:2.0, 1:1.0}),
        'word_char_neg3_v05': word_char({0:3.0, 1:1.0}),
    }


def prob(model, X):
    if hasattr(model, 'predict_proba'):
        return model.predict_proba(X)[:,1]
    raw=model.decision_function(X)
    return 1/(1+np.exp(-raw))


def pred(scores,t):
    return (np.asarray(scores)>=t).astype(int)


def hmean(vals):
    vals=[float(v) for v in vals]
    if any(v<=0 for v in vals): return 0.0
    return len(vals)/sum(1/v for v in vals)


def normalize(df, text_col):
    out=df.copy()
    out['text']=out[text_col].fillna('').astype(str).map(normalize_model_text)
    out=out[out['text'].str.len()>0].copy()
    out['template_group_id']=out['text'].map(canonical_template).map(short_hash)
    return out


def prepare_primary(path):
    d=normalize(pd.read_csv(path),'text')
    return d[d['split'].eq('development')].copy(), d[d['split'].eq('locked_test')].copy()


def prepare_imc(path):
    d=pd.read_csv(path)
    if not {'text','scam_type'} <= set(d.columns): raise SystemExit('IMC25 requires text,scam_type')
    d['family']=d['scam_type'].fillna('').astype(str).str.strip().str.casefold()
    d=d[(d['family']!='') & (d['family']!='spam')].copy()
    d=normalize(d,'text'); d['target']=1
    n=d.groupby('template_group_id')['family'].nunique()
    conflicts=set(n[n>1].index.astype(str))
    clean=d[~d['template_group_id'].astype(str).isin(conflicts)].copy()
    return d, clean, conflicts


def cap_imc(d, held=None, max_template=5, max_family=2000):
    w=d.copy()
    if held is not None: w=w[w['family']!=held].copy()
    w=w.groupby('template_group_id',group_keys=False).head(max_template).copy()
    parts=[]
    for _,g in w.groupby('family'):
        if len(g)>max_family: g=g.sample(n=max_family,random_state=42)
        parts.append(g)
    return pd.concat(parts,ignore_index=True) if parts else w.iloc[0:0].copy()


def prepare_financial(path):
    d=pd.read_csv(path)
    if not {'text','target'} <= set(d.columns): raise SystemExit('financial-prepared requires text,target')
    d=normalize(d,'text'); d=d[d['target'].astype(int).eq(0)].copy(); d['target']=0
    return d.drop_duplicates('template_group_id').copy()


def prepare_smishx(path):
    d=pd.read_csv(path)
    if not {'SMS','label'} <= set(d.columns): raise SystemExit('SmishX requires SMS,label')
    d['label_norm']=d['label'].astype(str).str.strip().str.casefold()
    d=d[d['label_norm'].eq('legitimate')].copy()
    d=normalize(d,'SMS'); d['target']=0
    return d.drop_duplicates('template_group_id').copy()


def clean_hardneg(primary_dev, imc_all, financial, smishx):
    primary_neg=set(primary_dev.loc[primary_dev['target'].astype(int).eq(0),'template_group_id'].astype(str))
    positives=set(primary_dev.loc[primary_dev['target'].astype(int).eq(1),'template_group_id'].astype(str)) | set(imc_all['template_group_id'].astype(str))
    financial=financial[~financial['template_group_id'].astype(str).isin(primary_neg|positives)].copy()
    fg=set(financial['template_group_id'].astype(str))
    smishx=smishx[~smishx['template_group_id'].astype(str).isin(primary_neg|positives|fg)].copy()
    return financial,smishx


def metric_bundle(y,p,s):
    cm=confusion_matrix(y,p,labels=[0,1]); tn,fp,fn,tp=cm.ravel()
    return {
      'f1_macro':float(f1_score(y,p,average='macro')),
      'precision_scam':float(precision_score(y,p,pos_label=1,zero_division=0)),
      'recall_scam':float(recall_score(y,p,pos_label=1,zero_division=0)),
      'f1_scam':float(f1_score(y,p,pos_label=1,zero_division=0)),
      'specificity':float(tn/(tn+fp)) if tn+fp else None,
      'average_precision':float(average_precision_score(y,s)),
      'balanced_accuracy':float(balanced_accuracy_score(y,p)),
      'confusion_matrix':cm.tolist(),
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--primary-manifest',required=True,type=Path)
    ap.add_argument('--imc25',required=True,type=Path)
    ap.add_argument('--financial-prepared',required=True,type=Path)
    ap.add_argument('--smishx-raw',required=True,type=Path)
    ap.add_argument('--reports-dir',default=Path('reports/v05'),type=Path)
    ap.add_argument('--models-dir',default=Path('models'),type=Path)
    ap.add_argument('--max-per-template',type=int,default=5)
    ap.add_argument('--max-per-family',type=int,default=2000)
    a=ap.parse_args(); a.reports_dir.mkdir(parents=True,exist_ok=True); a.models_dir.mkdir(parents=True,exist_ok=True)

    primary_dev,primary_locked=prepare_primary(a.primary_manifest)
    imc_all,imc_clean,imc_conflicts=prepare_imc(a.imc25)
    financial=prepare_financial(a.financial_prepared)
    smishx=prepare_smishx(a.smishx_raw)
    financial,smishx=clean_hardneg(primary_dev,imc_all,financial,smishx)
    modern_full=cap_imc(imc_clean,max_template=a.max_per_template,max_family=a.max_per_family)
    families=sorted(imc_clean['family'].unique())
    models=candidates()

    # Primary grouped OOF scores.
    X=primary_dev['text'].astype(str); y=primary_dev['target'].astype(int); g=primary_dev['template_group_id'].astype(str)
    cv=StratifiedGroupKFold(n_splits=5,shuffle=True,random_state=2026)
    primary={}
    for name,proto in models.items():
        oof=np.zeros(len(primary_dev))
        for tr,va in cv.split(X,y,g):
            assert not (set(g.iloc[tr]) & set(g.iloc[va]))
            m=clone(proto); m.fit(X.iloc[tr],y.iloc[tr]); oof[va]=prob(m,X.iloc[va])
        primary[name]={}
        for t in THRESHOLDS:
            p=pred(oof,t)
            primary[name][t]={
              'f1_macro':float(f1_score(y,p,average='macro')),
              'precision_scam':float(precision_score(y,p,pos_label=1,zero_division=0)),
              'recall_scam':float(recall_score(y,p,pos_label=1,zero_division=0)),
            }

    hardneg_all=pd.concat([financial[['text','target']],smishx[['text','target']]],ignore_index=True)

    # Positive family holdout.
    fam={name:{t:[] for t in THRESHOLDS} for name in models}
    for held in families:
        modern=cap_imc(imc_clean,held=held,max_template=a.max_per_template,max_family=a.max_per_family)
        test=imc_clean[imc_clean['family'].eq(held)].copy()
        assert not (set(modern['template_group_id'].astype(str)) & set(test['template_group_id'].astype(str)))
        train=pd.concat([primary_dev[['text','target']],modern[['text','target']],hardneg_all],ignore_index=True)
        for name,proto in models.items():
            m=clone(proto); m.fit(train['text'].astype(str),train['target'].astype(int)); s=prob(m,test['text'].astype(str))
            for t in THRESHOLDS:
                p=pred(s,t); fam[name][t].append({'family':held,'n':int(len(test)),'recall':float(np.mean(p==1)),'detected':int((p==1).sum()),'missed':int((p==0).sum())})

    # Leave-one-hard-negative-source-out.
    sources={'financial_ham':financial,'smishx_legitimate':smishx}
    neg={name:{t:[] for t in THRESHOLDS} for name in models}
    for held_name,held_df in sources.items():
        others=[df[['text','target']] for n,df in sources.items() if n!=held_name]
        train=pd.concat([primary_dev[['text','target']],modern_full[['text','target']],*others],ignore_index=True)
        for name,proto in models.items():
            m=clone(proto); m.fit(train['text'].astype(str),train['target'].astype(int)); s=prob(m,held_df['text'].astype(str))
            for t in THRESHOLDS:
                p=pred(s,t); spec=float(np.mean(p==0)); neg[name][t].append({'source':held_name,'n':int(len(held_df)),'specificity':spec,'false_positive_rate':1-spec})

    choices=[]
    for name in models:
      for t in THRESHOLDS:
        pm=primary[name][t]
        if pm['f1_macro']<0.94: continue
        fr=fam[name][t]; nr=neg[name][t]
        fm=float(np.mean([r['recall'] for r in fr])); fw=float(sum(r['recall']*r['n'] for r in fr)/sum(r['n'] for r in fr)); fmin=float(min(r['recall'] for r in fr))
        nm=float(np.mean([r['specificity'] for r in nr])); nmin=float(min(r['specificity'] for r in nr))
        choices.append({'model':name,'threshold':t,'primary_oof_f1_macro':pm['f1_macro'],'primary_oof_precision_scam':pm['precision_scam'],'primary_oof_recall_scam':pm['recall_scam'],'family_macro_recall':fm,'family_weighted_recall':fw,'family_min_recall':fmin,'negative_source_macro_specificity':nm,'negative_source_min_specificity':nmin,'selection_score':hmean([pm['f1_macro'],fm,nm])})

    selected=max(choices,key=lambda r:(r['selection_score'],r['negative_source_min_specificity'],r['family_macro_recall']))
    name=selected['model']; t=float(selected['threshold'])

    final_train=pd.concat([primary_dev[['text','target']],modern_full[['text','target']],financial[['text','target']],smishx[['text','target']]],ignore_index=True)
    final_model=clone(models[name]); final_model.fit(final_train['text'].astype(str),final_train['target'].astype(int))
    lx=primary_locked['text'].astype(str); ly=primary_locked['target'].astype(int); ls=prob(final_model,lx); lp=pred(ls,t)
    locked=metric_bundle(ly,lp,ls)

    model_path=a.models_dir/'scam_classifier_v05.joblib'; meta_path=a.models_dir/'scam_classifier_v05_metadata.json'
    joblib.dump(final_model,model_path)
    meta_path.write_text(json.dumps({'version':'0.5','model':name,'threshold':t,'selection':selected},indent=2),encoding='utf-8')

    report={'version':'0.5','development_sources':{'primary_development_rows':int(len(primary_dev)),'imc_capped_rows':int(len(modern_full)),'financial_ham_after_cross_source_dedup':int(len(financial)),'smishx_legitimate_after_cross_source_dedup':int(len(smishx)),'imc_family_conflict_groups_removed':int(len(imc_conflicts))},'selected':selected,'all_choices':sorted(choices,key=lambda r:r['selection_score'],reverse=True),'selected_family_results':fam[name][t],'selected_negative_source_results':neg[name][t],'primary_locked_test_after_selection':locked,'final_training_rows':int(len(final_train)),'final_training_class_counts':{str(k):int(v) for k,v in final_train['target'].value_counts().sort_index().items()},'model_path':str(model_path),'metadata_path':str(meta_path)}
    (a.reports_dir/'v05_model_selection.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__': main()
