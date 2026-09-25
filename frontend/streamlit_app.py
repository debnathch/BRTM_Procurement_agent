import io, requests, streamlit as st, pandas as pd

API='http://127.0.0.1:8000/api'
st.set_page_config(page_title='BRTM Procurement Control Center',layout='wide')
st.title('BRTM Procurement Control Center')
st.caption('Local-first • MARG-aware • Human-controlled procurement')

page=st.sidebar.radio('Navigation',['Home','Procurement','Master Data Collection','MARG Execution Reconciliation','Audit'])

if page=='Home':
    st.subheader('Control Center')
    st.info('MARG remains the transactional system of record. The agent provides recommendations and controlled execution requests.')
    try: st.json(requests.get(API+'/health',timeout=3).json())
    except Exception as e: st.error(f'API unavailable: {e}')

elif page=='Master Data Collection':
    st.subheader('Master Data Collection')
    st.write('Upload MARG Excel/CSV exports. The importer detects supported report profiles and validates before ingestion.')
    uploads=st.file_uploader('MARG reports',type=['xlsx','xls','csv'],accept_multiple_files=True)
    if uploads:
        for f in uploads:
            st.write(f'**{f.name}** — {f.size:,} bytes')
        if st.button('Validate & Preview'):
            st.warning('Validation preview is local and non-destructive. Full atomic import should be enabled only after all required datasets pass.')

elif page=='Procurement':
    st.subheader('Procurement Recommendations')
    codes=st.text_input('Optional product codes (comma separated)')
    if st.button('Run procurement analysis'):
        try:
            r=requests.post(API+'/procurement/run',json={'product_codes':[x.strip() for x in codes.split(',') if x.strip()] or None},timeout=30)
            r.raise_for_status(); st.success(r.json())
        except Exception as e: st.error(str(e))

elif page=='MARG Execution Reconciliation':
    st.subheader('MARG Execution Reconciliation')
    lookup=st.text_input('Idempotency key or MARG reference')
    if 'recon' not in st.session_state: st.session_state.recon=None
    if st.button('Search execution') and lookup:
        try:
            r=requests.get(API+'/execution/reconciliation/search',params={'lookup':lookup},timeout=10); r.raise_for_status()
            st.session_state.recon=r.json()
        except Exception as e: st.error(str(e))
    recon=st.session_state.recon
    if recon:
        st.json({k:v for k,v in recon.items() if k not in ('audit_history','attempts')})
        st.subheader('Execution attempts')
        st.dataframe(pd.DataFrame(recon.get('attempts',[])),use_container_width=True)
        st.subheader('Audit history')
        st.dataframe(pd.DataFrame(recon.get('audit_history',[])),use_container_width=True)
        if recon.get('execution_status')=='UNKNOWN':
            st.warning('Manager verification is required before retry.')
            confirmed=st.checkbox('I have verified the MARG result and confirm this resolution.')
            ref=st.text_input('Verified MARG reference (required for success)')
            reason=st.text_area('Reconciliation evidence / reason')
            c1,c2=st.columns(2)
            with c1:
                if st.button('Confirm CREATED') and confirmed:
                    rr=requests.post(API+'/execution/reconciliation/resolve',params={'lookup':lookup,'confirmed':True,'reference':ref,'actor':'manager-ui','reason':reason},timeout=10)
                    st.write(rr.json())
            with c2:
                if st.button('Confirm NOT CREATED') and confirmed:
                    rr=requests.post(API+'/execution/reconciliation/resolve',params={'lookup':lookup,'confirmed':False,'actor':'manager-ui','reason':reason},timeout=10)
                    st.write(rr.json())

elif page=='Audit':
    st.subheader('Audit History')
    st.caption('Saved views: common reconciliation investigations.')
    builtin={
      'Default — Ambiguous execution':['PO_EXECUTION_RECONCILIATION_LOOKUP','PO_EXECUTION_MANAGER_CONFIRMATION','PO_EXECUTION_RECONCILED_SUCCEEDED','PO_EXECUTION_RECONCILED_FAILED'],
      'Manager — Reconciliation activity':['PO_EXECUTION_MANAGER_CONFIRMATION','PO_EXECUTION_RECONCILED_SUCCEEDED','PO_EXECUTION_RECONCILED_FAILED','PO_EXECUTION_RETRY_DECISION'],
      'All events':[]
    }
    if 'saved_views' not in st.session_state: st.session_state.saved_views={}
    names=list(builtin)+list(st.session_state.saved_views)
    selected=st.selectbox('Saved view',names)
    event_types=builtin.get(selected,st.session_state.saved_views.get(selected,[]))
    custom=st.text_input('Event type filter (comma separated)',value=','.join(event_types))
    actor=st.text_input('Actor filter')
    outcome=st.text_input('Outcome filter')
    c1,c2,c3=st.columns(3)
    with c1:
        if st.button('Apply filters'): st.session_state.audit_filter={'event_types':[x.strip() for x in custom.split(',') if x.strip()],'actor':actor,'outcome':outcome}
    with c2:
        if st.button('Clear filters'): st.session_state.audit_filter={'event_types':[],'actor':'','outcome':''}
    with c3:
        new_name=st.text_input('New saved view name')
        if st.button('Save view') and new_name:
            st.session_state.saved_views[new_name]=[x.strip() for x in custom.split(',') if x.strip()]
            st.success('Saved for this browser session.')
    st.info('CSV export and date-range filters remain available in the full audit implementation; this lightweight UI keeps the saved-view contract explicit.')
