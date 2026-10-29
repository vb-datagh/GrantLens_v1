"""Auditable grant pipeline transformations; no remote services."""
import sqlite3
from contextlib import closing
import numpy as np
import pandas as pd

REQUIRED = ['funder', 'program', 'type', 'status', 'amount', 'fit_score', 'deadline']
STATUSES = ['Research', 'Qualified', 'Preparing', 'Submitted', 'Awarded', 'Declined']


def prepare(raw, as_of):
    missing = set(REQUIRED) - set(raw.columns)
    if missing:
        raise ValueError('Missing columns: ' + ', '.join(sorted(missing)))
    df = raw[REQUIRED].copy().reset_index(drop=True)
    issues = []
    for col in ['funder', 'program', 'type', 'status']:
        df[col] = df[col].fillna('').astype(str).str.strip()
    for col in ['amount', 'fit_score']:
        original = df[col].copy()
        df[col] = pd.to_numeric(df[col], errors='coerce')
        invalid = ~np.isfinite(df[col]) | (df[col] < 0)
        if col == 'fit_score':
            invalid |= df[col] > 100
        for i in df.index[invalid]:
            issues.append((i + 2, col, 'Missing or invalid numeric value', str(original[i])))
        df.loc[invalid, col] = np.nan
    dates = pd.to_datetime(df.deadline, format='%Y-%m-%d', errors='coerce')
    for i in df.index[dates.isna()]:
        issues.append((i + 2, 'deadline', 'Missing or invalid ISO date; timing unknown', str(df.loc[i, 'deadline'])))
    df['deadline'] = dates
    for col in ['funder', 'program', 'type']:
        for i in df.index[df[col].eq('')]:
            issues.append((i + 2, col, 'Missing text', ''))
    for i in df.index[~df.status.isin(STATUSES)]:
        issues.append((i + 2, 'status', 'Unknown pipeline status', df.loc[i, 'status']))
    duplicates = df.duplicated(['funder', 'program'], keep=False)
    for i in df.index[duplicates]:
        issues.append((i + 2, 'program', 'Repeated funder/program; excluded until resolved', df.loc[i, 'program']))
    df['eligible_for_metrics'] = ~duplicates & df.funder.ne('') & df.program.ne('') & df.status.isin(STATUSES)
    df['days_left'] = (df.deadline - pd.Timestamp(as_of)).dt.days
    df['active'] = df.status.isin(STATUSES[:4])
    df['actionable'] = df.active & (df.days_left.ge(0) | df.days_left.isna())
    # Deadline urgency contributes only when timing is known. Missing fit is unranked.
    urgency = (1 - df.days_left.clip(0, 90) / 90).fillna(0) * 100
    df['priority'] = (df.fit_score * .8 + urgency * .2).round(1).where(df.actionable)
    df['next_action'] = 'Review outcome'
    df.loc[df.active, 'next_action'] = 'Research and qualify'
    df.loc[df.active & df.days_left.isna(), 'next_action'] = 'Verify deadline'
    df.loc[df.active & df.days_left.lt(0), 'next_action'] = 'Resolve past deadline'
    df.loc[df.active & df.days_left.between(0, 30), 'next_action'] = 'Review near-term application'
    return df, pd.DataFrame(issues, columns=['csv_row', 'field', 'issue', 'input'])


def pipeline_sql(df):
    """Run the same SQL shown in the app against the selected, valid records."""
    with closing(sqlite3.connect(':memory:')) as con:
        df[['status', 'amount']].to_sql('prospects', con, index=False)
        return pd.read_sql_query(PIPELINE_SQL, con)


PIPELINE_SQL = '''SELECT status, COUNT(*) AS prospects,
       COUNT(amount) AS known_amounts,
       SUM(amount) AS potential_amount
FROM prospects
GROUP BY status
ORDER BY prospects DESC, status;'''


def safe_csv(df):
    """Prevent imported text from becoming formulas in spreadsheet exports."""
    out = df.copy()
    for col in out.select_dtypes(include=['object', 'string']).columns:
        out[col] = out[col].map(lambda v: "'" + v if isinstance(v, str) and v.lstrip().startswith(('=', '+', '-', '@')) else v)
    return out.to_csv(index=False).encode('utf-8')
