import requests,streamlit as st,pandas as pd
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
    st.subheader('MARG Master Data Collection')
    uploads=st.file_uploader('Upload MARG reports',type=['xlsx','xls','csv'],accept_multiple_files=True)
    for f in uploads or []: st.write(f'**{f.name}** — {f.size:,} bytes')
    if uploads and st.button('Validate & Preview'):
        for f in uploads:
            try:
                r=requests.post(API+'/ingestion/validate',files={'file':(f.name,f.getvalue(),f.type)},timeout=30)
                r.raise_for_status(); data=r.json()
                st.write(f'### {f.name}')
                st.json({'dataset':data['dataset'],'rows':data['rows'],'errors':data['errors'],'warnings':data['warnings']})
                if data['preview']: st.dataframe(pd.DataFrame(data['preview']),use_container_width=True)
            except Exception as e: st.error(str(e))
    st.caption('Validation is non-destructive. A future atomic three-file import can replace the operational snapshot only after all datasets pass validation.')

elif page=='Procurement':
    st.subheader('Procurement Recommendations')
    codes=st.text_input('Optional product codes (comma separated)')
    if st.button('Run procurement analysis'):
        try:
            r=requests.post(API+'/procurement/run',json={'product_codes':[x.strip() for x in codes.split(',') if x.strip()] or None},timeout=30);r.raise_for_status();st.success(r.json())
        except Exception as e:st.error(str(e))

elif page=='MARG Execution Reconciliation':
    st.subheader('MARG Execution Reconciliation')
    lookup=st.text_input('Idempotency key or MARG reference')
    if 'recon' not in st.session_state: st.session_state.recon=None
    if st.button('Search execution') and lookup:
        try:
            r=requests.get(API+'/execution/reconciliation/search',params={'lookup':lookup},timeout=10);r.raise_for_status();st.session_state.recon=r.json()
        except Exception as e:st.error(str(e))
    recon=st.session_state.recon
    if recon:
        st.json({k:v for k,v in recon.items() if k not in ('audit_history','attempts')})
        st.dataframe(pd.DataFrame(recon.get('attempts',[])),use_container_width=True)
        st.dataframe(pd.DataFrame(recon.get('audit_history',[])),use_container_width=True)
        if recon.get('execution_status')=='UNKNOWN':
            st.warning('Manager verification is required before retry.')
            confirmed=st.checkbox('I have verified the MARG result and confirm this resolution.')
            ref=st.text_input('Verified MARG reference')
            reason=st.text_area('Reconciliation evidence / reason')
            c1,c2=st.columns(2)
            with c1:
                if st.button('Confirm CREATED') and confirmed:
                    rr=requests.post(API+'/execution/reconciliation/resolve',params={'lookup':lookup,'confirmed':True,'reference':ref,'actor':'manager-ui','reason':reason},timeout=10);st.write(rr.json())
            with c2:
                if st.button('Confirm NOT CREATED') and confirmed:
                    rr=requests.post(API+'/execution/reconciliation/resolve',params={'lookup':lookup,'confirmed':False,'actor':'manager-ui','reason':reason},timeout=10);st.write(rr.json())

elif page=='Audit':
    st.subheader('Audit History')
    builtin={
      'Default — Ambiguous execution':['PO_EXECUTION_RECONCILIATION_LOOKUP','PO_EXECUTION_MANAGER_CONFIRMATION','PO_EXECUTION_RECONCILED_SUCCEEDED','PO_EXECUTION_RECONCILED_FAILED'],
      'Manager — Reconciliation activity':['PO_EXECUTION_MANAGER_CONFIRMATION','PO_EXECUTION_RECONCILED_SUCCEEDED','PO_EXECUTION_RECONCILED_FAILED','PO_EXECUTION_RETRY_DECISION'],
      'All events':[]
    }
    if 'saved_views' not in st.session_state: st.session_state.saved_views={}
    selected=st.selectbox('Saved view',list(builtin)+list(st.session_state.saved_views))
    default_types=builtin.get(selected,st.session_state.saved_views.get(selected,[]))
    event_types=st.text_input('Event type filter (comma separated)',value=','.join(default_types))
    actor=st.text_input('Actor filter')
    outcome=st.text_input('Outcome filter')
    if st.button('Apply filters'):
        params={'event_type':event_types,'actor':actor,'outcome':outcome}
        try:
            r=requests.get(API+'/audit/events',params=params,timeout=10);r.raise_for_status();st.session_state.audit_rows=r.json()['events']
        except Exception as e:st.error(str(e))
    if st.button('Clear filters'): st.session_state.audit_rows=[]
    new_name=st.text_input('New saved view name')
    if st.button('Save view') and new_name:
        st.session_state.saved_views[new_name]=[x.strip() for x in event_types.split(',') if x.strip()]
    rows=st.session_state.get('audit_rows',[])
    st.write(f'{len(rows)} audit events')
    if rows:
        st.dataframe(pd.DataFrame(rows),use_container_width=True)
        csv=requests.get(API+'/audit/events.csv',params={'event_type':event_types,'actor':actor,'outcome':outcome},timeout=10).text
        st.download_button('Export filtered audit history (CSV)',csv,file_name='audit_history.csv',mime='text/csv')
