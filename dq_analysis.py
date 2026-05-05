# ============================================================
# DATA QUALITY ANALYSIS ENGINE
# Author: Rounak Mishra
# ============================================================

import pandas as pd
import numpy as np
from datetime import datetime


def load_data(filepath):
    try:
        df = pd.read_csv(filepath, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(filepath, encoding='latin-1')
    return df


def score_completeness(df):
    total_cells = df.shape[0] * df.shape[1]
    null_cells = df.isnull().sum().sum()
    non_null = total_cells - null_cells
    score = round((non_null / total_cells) * 100, 2)
    col_completeness = (1 - df.isnull().mean()) * 100
    return {
        'score': score,
        'total_cells': total_cells,
        'null_cells': int(null_cells),
        'missing_pct': round((null_cells / total_cells) * 100, 2),
        'col_breakdown': col_completeness.round(2).to_dict()
    }


def score_uniqueness(df):
    total_rows = len(df)
    duplicate_rows = df.duplicated().sum()
    unique_rows = total_rows - duplicate_rows
    score = round((unique_rows / total_rows) * 100, 2)
    return {
        'score': score,
        'total_rows': total_rows,
        'duplicate_rows': int(duplicate_rows),
        'unique_rows': int(unique_rows),
        'duplicate_pct': round((duplicate_rows / total_rows) * 100, 2)
    }


def score_consistency(df):
    inconsistent_cols = []
    consistency_details = {}
    for col in df.columns:
        col_data = df[col].dropna()
        if col_data.dtype == 'object':
            numeric_count = pd.to_numeric(col_data, errors='coerce').notna().sum()
            text_count = len(col_data) - numeric_count
            if numeric_count > 0 and text_count > 0:
                inconsistent_cols.append(col)
                consistency_details[col] = {
                    'numeric_entries': int(numeric_count),
                    'text_entries': int(text_count)
                }
            unique_vals = col_data.unique()
            lower_vals = [str(v).lower() for v in unique_vals]
            if len(set(lower_vals)) < len(set([str(v) for v in unique_vals])):
                if col not in inconsistent_cols:
                    inconsistent_cols.append(col)
    total_cols = len(df.columns)
    consistent_cols = total_cols - len(inconsistent_cols)
    score = round((consistent_cols / total_cols) * 100, 2)
    return {
        'score': score,
        'total_cols': total_cols,
        'consistent_cols': consistent_cols,
        'inconsistent_cols': inconsistent_cols,
        'details': consistency_details
    }


def score_validity(df):
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    invalid_counts = {}
    total_invalid = 0
    total_numeric_cells = 0
    for col in numeric_cols:
        col_data = df[col].dropna()
        if len(col_data) > 0:
            Q1 = col_data.quantile(0.25)
            Q3 = col_data.quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - 3 * IQR
            upper = Q3 + 3 * IQR
            outliers = col_data[(col_data < lower) | (col_data > upper)]
            invalid_counts[col] = int(len(outliers))
            total_invalid += len(outliers)
            total_numeric_cells += len(col_data)
    if total_numeric_cells > 0:
        score = round((1 - total_invalid / total_numeric_cells) * 100, 2)
    else:
        score = 100.0
    return {
        'score': score,
        'numeric_cols': numeric_cols,
        'invalid_counts': invalid_counts,
        'total_invalid': total_invalid
    }


def score_accuracy(df):
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    inaccurate = {}
    total_inaccurate = 0
    total_checked = 0
    for col in numeric_cols:
        col_data = df[col].dropna()
        negative_count = (col_data < 0).sum()
        if negative_count > 0:
            inaccurate[col] = int(negative_count)
            total_inaccurate += negative_count
        total_checked += len(col_data)
    if total_checked > 0:
        score = round((1 - total_inaccurate / total_checked) * 100, 2)
    else:
        score = 100.0
    return {
        'score': score,
        'inaccurate_cols': inaccurate,
        'total_inaccurate': int(total_inaccurate)
    }


def score_timeliness(df):
    date_cols = []
    timeliness_info = {}
    for col in df.columns:
        if any(word in col.lower() for word in
               ['date', 'time', 'year', 'month', 'created', 'updated']):
            date_cols.append(col)
    if date_cols:
        col = date_cols[0]
        try:
            dates = pd.to_datetime(df[col], errors='coerce').dropna()
            if len(dates) > 0:
                most_recent = dates.max()
                oldest = dates.min()
                days_old = (datetime.now() - most_recent).days
                score = max(0, min(100, 100 - (days_old / 365) * 10))
                timeliness_info = {
                    'date_col': col,
                    'most_recent': str(most_recent.date()),
                    'oldest': str(oldest.date()),
                    'days_since_latest': days_old
                }
                return {
                    'score': round(score, 2),
                    'info': timeliness_info,
                    'has_dates': True
                }
        except:
            pass
    return {
        'score': 75.0,
        'info': {'note': 'No date column detected'},
        'has_dates': False
    }


def run_full_dq_assessment(filepath):
    df = load_data(filepath)
    results = {
        'dataset_info': {
            'rows': len(df),
            'columns': len(df.columns),
            'col_names': df.columns.tolist(),
            'dtypes': df.dtypes.astype(str).to_dict()
        },
        'completeness': score_completeness(df),
        'uniqueness': score_uniqueness(df),
        'consistency': score_consistency(df),
        'validity': score_validity(df),
        'accuracy': score_accuracy(df),
        'timeliness': score_timeliness(df),
        'dataframe': df
    }
    scores = [
        results['completeness']['score'],
        results['uniqueness']['score'],
        results['consistency']['score'],
        results['validity']['score'],
        results['accuracy']['score'],
        results['timeliness']['score']
    ]
    results['overall_score'] = round(np.mean(scores), 2)
    return results


if __name__ == '__main__':
    results = run_full_dq_assessment('dataset.csv')
    print(f"Overall DQ Score: {results['overall_score']}%")
    print(f"Completeness:     {results['completeness']['score']}%")
    print(f"Uniqueness:       {results['uniqueness']['score']}%")
    print(f"Consistency:      {results['consistency']['score']}%")
    print(f"Validity:         {results['validity']['score']}%")
    print(f"Accuracy:         {results['accuracy']['score']}%")
    print(f"Timeliness:       {results['timeliness']['score']}%")