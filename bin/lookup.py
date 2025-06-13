#!/usr/bin/env python3
import click
from sqlalchemy import create_engine, event, text
import pandas as pd
import numpy as np
# import matplotlib.pyplot as plt

@click.command()
@click.option( "--participant_id", type=int, required=True,)
@click.option( "--ae_ana", required=True,)
@click.option( "--ae_con", required=True,)
@click.option( "--ae_inv", required=True,)
@click.option( "--ae_side", required=True,)
@click.option( "--ae_tre", required=True,)
@click.option( "--icd10", required=True,)
@click.option( "--opcs", required=True,)
@click.option( "--snomed", required=True,)

def query(participant_id, ae_ana, ae_con, ae_inv, ae_side, ae_tre, icd10, opcs, snomed):

    version = "source_data_100kv16_covidv4"
    
    def query_to_df(sql_query, version):
        database = "gel_clinical_cb_sql_pro"
        host = "clinical-cb-sql-pro.cfe5cdx3wlef.eu-west-2.rds.amazonaws.com"
        port = 5432
        password = 'anXReTz36Q5r'
        user = 'jupyter_notebook'
        engine = create_engine(f'''postgresql://{user}:{password}@{host}:{port}/{database}''')

        @event.listens_for(engine, "connect", insert=True)
        def set_search_path(dbapi_connection, connection_record):
            existing_autocommit = dbapi_connection.autocommit
            dbapi_connection.autocommit = True
            cursor = dbapi_connection.cursor()
            cursor.execute(f"SET SESSION search_path={version}")
            cursor.close()
            dbapi_connection.autocommit = existing_autocommit
        
        with engine.connect() as connection:
            result = connection.execute(text(sql_query))
            return(pd.DataFrame(result))
    
    def about(participant_id: int):

        about_sql = (f'''
            SELECT ps.participant_id, 
                ps.participant_phenotyped_sex, 
                ps.participant_karyotyped_sex, 
                ps.yob, 
                ps.genetically_inferred_ancestry_thr,
                p.participant_ethnic_category,
                ps.programme
            FROM
                key_columns as ps,
                participant as p
            WHERE
                ps.participant_id = p.participant_id
            AND
                ps.participant_id = {participant_id}
            ''')
        about_query = query_to_df(about_sql, version)
        return (f'''
            <h1>About</h1>
            <table>
            <tr><td>Participant ID</td><td>{participant_id}</td></tr>
            <tr><td>Year of birth</td><td>{about_query.loc[0, 'yob']}</td></tr>
            <tr><td>Phenotyped sex</td><td>{about_query.loc[0, 'participant_phenotyped_sex']}</td></tr>
            <tr><td>Karyotyped sex</td><td>{about_query.loc[0, 'participant_karyotyped_sex']}</td></tr>
            <tr><td>Genomic ancestry</td><td>{about_query.loc[0, 'genetically_inferred_ancestry_thr']}</td></tr>
            <tr><td>Stated ethnicity</td><td>{about_query.loc[0, 'participant_ethnic_category']}</td></tr>
            <tr><td>Programme</td><td>{about_query.loc[0, 'programme']}</td></tr>
            </table>
            ''')
    
    def family(participant_id: int):
        type_sql = (f''' SELECT participant_type
            FROM key_columns
            WHERE participant_id = {participant_id}
            ''')
        type_query = query_to_df(type_sql, version)
        type = type_query.loc[0, 'participant_type']
        if (type == 'rd_proband'):
            proband_sql = (f'''SELECT
                    pm.participant_id,
                    pm.rare_diseases_pedigree_member_id,
                    pm.phenotypic_sex,
                    pm.affection_status,
                    pm.proband,
                    pm.mother_id,
                    pm.father_id,
                    f.family_group_type
                FROM 
                    rare_diseases_pedigree as p,
                    rare_diseases_pedigree_member as pm,
                    rare_diseases_family as f
                WHERE p.pedigree_proband_participant_id = {participant_id}
                AND p.rare_diseases_family_sk = pm.rare_diseases_family_sk
                AND f.rare_diseases_family_sk = pm.rare_diseases_family_sk
            ''')
            proband_query = query_to_df(proband_sql, version)
            return family_processing(proband_query, participant_id).to_html()
        elif (type == 'rd_relative'):
            relative_sql = (f''' SELECT
                    pm.participant_id,
                    pm.rare_diseases_pedigree_member_id,
                    pm.relationship_to_proband,
                    pm.phenotypic_sex,
                    pm.affection_status,
                    pm.proband,
                    pm.mother_id,
                    pm.father_id,
                    f.family_group_type
                FROM 
                    rare_diseases_pedigree_member as pm,
                    rare_diseases_family as f
                WHERE
                    pm.rare_diseases_family_sk IN (
                        SELECT pm.rare_diseases_family_sk
                        FROM rare_diseases_pedigree_member as pm
                        WHERE participant_id = {participant_id}
                    )
                AND f.rare_diseases_family_sk = pm.rare_diseases_family_sk
            ''')
            relative_query= query_to_df(relative_sql, version)
            return family_processing(relative_query, participant_id).to_html()
        elif (type == 'cancer_participant'):
            return ("<p>No family data for cancer participants</p>")
    
    def family_processing(query, participant_id):
            query['selected'] = ''
            query.loc[query['participant_id'] == participant_id, 'selected'] = '*'
            query['relationship_to_proband'] = 'unknown'
            query.loc[query['proband'] == True, 'relationship_to_proband'] = 'Proband'
            proband_mother = query.loc[query['proband'] == True, 'mother_id'].item()
            proband_father = query.loc[query['proband'] == True, 'father_id'].item()
            query.loc[query['rare_diseases_pedigree_member_id'] == proband_mother, 'relationship_to_proband'] = 'Mother'
            query.loc[query['rare_diseases_pedigree_member_id'] == proband_father, 'relationship_to_proband'] = 'Father'
            query.loc[(query['father_id'] == proband_father) & (query['mother_id'] == proband_mother) & (query['proband'] == False), 'relationship_to_proband'] = 'Full sibling'
            query.loc[(query['father_id'] != proband_father) & (query['mother_id'] == proband_mother) & (query['proband'] == False), 'relationship_to_proband'] = 'Half sibling'
            query.loc[(query['father_id'] == proband_father) & (query['mother_id'] != proband_mother) & (query['proband'] == False), 'relationship_to_proband'] = 'Half sibling'
            query = query[['selected', 'relationship_to_proband', 'family_group_type', 'participant_id', 'rare_diseases_pedigree_member_id', 'phenotypic_sex', 'affection_status']]
            return query

    def genomic (participant_id: int):
        genomic_df = pd.DataFrame()
        gfpt_sql = (f'''SELECT platekey, genome_build, type, file_path, file_type, file_sub_type
            FROM genome_file_paths_and_types
            WHERE participant_id = {participant_id}''')
        gfpt_query = query_to_df(gfpt_sql, version)
        if not gfpt_query.empty:
            gfpt_query['source'] = "100kGP short reads"
            genomic_df = pd.concat([genomic_df, gfpt_query], ignore_index=True)
        lrs_sql = (f'''SELECT laboratory_sample_id as platekey, experiment_type as source, genome_version as genome_build, bam_file as file_path
            FROM lrs_sequencing_data
            WHERE participant_id = {participant_id}''')
        lrs_query = query_to_df(lrs_sql, version)
        if not lrs_query.empty:
            lrs_query['file_type'] = 'Assembly'
            lrs_query['file_sub_type'] = 'BAM'
            genomic_df = pd.concat([genomic_df, lrs_query], ignore_index=True)
        cancer_sql = (f'''SELECT *
            FROM cancer_100K_genomes_realigned_on_pipeline_2
            WHERE participant_id = {participant_id}''')
        cancer_query = query_to_df(cancer_sql, version)
        if not cancer_query.empty:
            for index, row in cancer_query.iterrows():
                new_can = pd.DataFrame({
                    "platekey":[row['tumour_sample_platekey'], row['germline_sample_platekey'], row['tumour_sample_platekey'], row['germline_sample_platekey'], row['tumour_sample_platekey'], row['germline_sample_platekey'], row['tumour_sample_platekey'], row['germline_sample_platekey'], row['tumour_sample_platekey'], row['tumour_sample_platekey'], row['tumour_sample_platekey'], row['germline_sample_platekey']],
                    "type": ['cancer somatic', 'cancer germline', 'cancer somatic', 'cancer germline', 'cancer somatic', 'cancer germline', 'cancer somatic', 'cancer germline', 'cancer somatic', 'cancer somatic', 'cancer somatic', 'cancer germline'],
                    "file_path": [row['tumour_cram'], row['germline_cram'], row['somatic_small_variants_vcf_path'], row['germline_small_variants_vcf_path'], row['somatic_sv_vcf'], row['germline_sv_vcf'], row['somatic_cnv_vcf'], row['germline_cnv_vcf'], row['somatic_pindel_vcf'], row['somatic_small_variants_annotation_vcf'], row['tinc_result'], row['germline_small_variants_hard_filtered_vcf_path']],
                    "file_type": ['Assembly', 'Assembly', 'Variations', 'Variations', 'Variations', 'Variations', 'Variations', 'Variations', 'Variations', 'Variations', 'TINC', 'Variations'],
                    "file_sub_type": ['CRAM', 'CRAM', 'Standard VCF', 'Standard VCF', 'Structural VCF', 'Structural VCF', 'CNV VCF', 'CNV VCF', 'Pindel', 'Annotated VCF', 'TINC result', 'Standard VCF hard-filtered']
                })
                new_can['genome_build'] = 'GRCh38'
                new_can['source'] = 'Cancer realigned on dragen2'
                genomic_df = pd.concat([genomic_df, new_can], ignore_index=True)
            
        return genomic_df.to_html()

    def column_separate(table, column, convert_table):
        table[column] = table[column].str.split("|")
        table = table.explode(column)
        table = table.replace(r'^\s*$', np.nan, regex=True)
        table = table.dropna(subset=[column])
        table['date']= pd.to_datetime(table['date'])
        convert = pd.read_csv(convert_table,sep = '\t', dtype=str)
        table = pd.merge(table, convert, how = "left", left_on=column, right_on = 'coding')
        table = table[['participant_id', 'date', column, 'meaning']]
        return table
    
    def diag_ae_separate(diag_table):
        diag_table['diag_all'] = diag_table['diag_all'].str.split("|")
        diag_table['diag2_all'] = diag_table['diag2_all'].str.split("|")
        diag_table['diaga_all'] = diag_table['diaga_all'].str.split("|")
        diag_table['diags_all'] = diag_table['diags_all'].str.split("|")
        diag_table = diag_table.explode(['diag_all', 'diag2_all', 'diaga_all', 'diags_all'])
        diag_table = diag_table.replace(r'^\s*$', np.nan, regex=True)
        diag_table = diag_table.dropna(subset=['diag_all'])
        diag_table['date']= pd.to_datetime(diag_table['date'])
        return diag_table

    def diagnoses (part_id):
    
        diag_table = pd.DataFrame()
        
        ae_sql = (f'''
        SELECT participant_id, arrivaldate as date, diag_all, diag2_all, diaga_all, diags_all
        FROM hes_ae
        WHERE participant_id = {part_id}
        ''')
        ae_query = query_to_df(ae_sql, version)
        if not ae_query.empty:
            ae_query = diag_ae_separate(ae_query)
            ae_con = pd.read_csv(ae_con,sep = '\t')
            ae_ana = pd.read_csv(ae_ana,sep = '\t')
            ae_side = pd.read_csv(ae_side,sep = '\t')
            ae_side = ae_side.astype({'side_code': object})
            ae_query = ae_query.astype({'diags_all': object})
            ae_query[['diag2_all', 'diaga_all']] = ae_query[['diag2_all', 'diaga_all']].apply(pd.to_numeric)
            ae_query = pd.merge(ae_query, ae_con, how = "left", left_on='diag2_all', right_on = 'con_code')
            ae_query = pd.merge(ae_query, ae_ana, how = "left", left_on='diaga_all', right_on = 'ana_code')
            ae_query = pd.merge(ae_query, ae_side, how = "left", left_on='diags_all', right_on = 'side_code')
            ae_query['meaning'] = ae_query['con_meaning'].fillna('') + ', ' + ae_query['ana_meaning'].fillna('') + ', ' + ae_query['side_meaning'].fillna('')
            ae_query = ae_query[['participant_id', 'date', 'diag_all', 'meaning']]
            ae_query['source'] = 'Accident and Emergency: A&E diagnosis code'
            diag_table = pd.concat([diag_table, ae_query])
        
        apc_sql = (f'''
            SELECT participant_id, admidate as date, diag_all
            FROM hes_apc
            WHERE participant_id = {part_id}
            ''')
        apc_query = query_to_df(apc_sql, version)
        if not apc_query.empty:
            apc_query = column_separate(apc_query, 'diag_all', icd10)
            apc_query['source'] = 'Admitted patient care: ICD10 code'
            diag_table = pd.concat([diag_table, apc_query])
        
        op_sql = (f'''
            SELECT participant_id, apptdate as date, diag_all
            FROM hes_op
            WHERE participant_id = {part_id}
            ''')
        op_query = query_to_df(op_sql, version)
        if not op_query.empty:
            op_query = column_separate(op_query, 'diag_all', icd10)
            op_query['source'] = 'Outpatients: ICD10 code'
            diag_table = pd.concat([diag_table, op_query])
        
        ecds_sql = (f'''
            SELECT participant_id, seen_date as date, diagnosis_code_all as diag_all
            FROM ecds
            WHERE participant_id = {part_id}
            ''')
        ecds_query = query_to_df(ecds_sql, version)
        if not ecds_query.empty:
            ecds_query = column_separate(ecds_query, 'diag_all', snomed)
            ecds_query['source'] = 'Emergency care dataset: SNOMED CT'
            diag_table = pd.concat([diag_table, ecds_query])
        
        diag_table['event'] = diag_table['diag_all'] + ": " + diag_table['meaning']
        
        return (diag_table[['participant_id', 'date', 'event', 'source']])
        
    def investigations (part_id):
    
        invest_table = pd.DataFrame()
        
        ae_invest_sql = (f'''
            SELECT participant_id, arrivaldate as date, invest_all
            FROM hes_ae
            WHERE participant_id = {part_id}
            ''')
        ae_invest_query = query_to_df(ae_invest_sql, version)
        if not ae_invest_query.empty:
            ae_invest_query = column_separate(ae_invest_query, 'invest_all', ae_inv)
            ae_invest_query['source'] = 'Accident and Emergency: A&E investigation code'
            invest_table = pd.concat([ae_invest_query, invest_table])
        
        did_invest_sql = (f'''
            SELECT participant_id, did_date3 as date, did_snomedct_code invest_all
            FROM did
            WHERE participant_id = {part_id}
            ''')
        did_invest_query = query_to_df(did_invest_sql, version)
        if not did_invest_query.empty:
            did_invest_query = column_separate(did_invest_query, 'invest_all', snomed)
            did_invest_query['source'] = 'Diagnostic imaging data: SNOMED CT code'
            invest_table = pd.concat([did_invest_query, invest_table])
        
        ecds_invest_sql = (f'''
            SELECT participant_id, seen_date as date, investigation_code_all as invest_all
            FROM ecds
            WHERE participant_id = {part_id}
            ''')
        ecds_invest_query = query_to_df(ecds_invest_sql, version)
        if not ecds_invest_query.empty:
            ecds_invest_query = column_separate(ecds_invest_query, 'invest_all', snomed)
            ecds_invest_query['source'] = 'Emergency care dataset: SNOMED CT code'
            invest_table = pd.concat([ecds_invest_query, invest_table])
    
        invest_table['event'] = invest_table['invest_all'] + ": " + invest_table['meaning']
        
        return (invest_table[['participant_id', 'date', 'event', 'source']])

    def treatments (part_id):

        treat_table = pd.DataFrame()
        
        ae_treat_sql = (f'''
            SELECT participant_id, arrivaldate as date, treat_all
            FROM hes_ae
            WHERE participant_id = {part_id}
            ''')
        ae_treat_query = query_to_df(ae_treat_sql, version)
        if not ae_treat_query.empty:
            ae_treat_query = column_separate(ae_treat_query, 'treat_all', ae_tre)
            ae_treat_query = ae_treat_query[['participant_id', 'date', 'treat_all', 'meaning']]
            ae_treat_query['source'] = 'Accident and Emergency: A&E treatment code'
            treat_table = pd.concat([ae_treat_query, treat_table])
        
        apc_treat_sql = (f'''
            SELECT participant_id, admidate as date, opertn_all as treat_all
            FROM hes_apc
            WHERE participant_id = {part_id}
            ''')
        apc_treat_query = query_to_df(apc_treat_sql, version)
        if not apc_treat_query.empty:
            apc_treat_query = column_separate(apc_treat_query, 'treat_all', opcs)
            apc_treat_query['source'] = 'Admitted Patient Care: OPCS4'
            treat_table = pd.concat([apc_treat_query, treat_table])
        
        op_treat_sql = (f'''
            SELECT participant_id, apptdate as date, opertn_all as treat_all
            FROM hes_op
            WHERE participant_id = {part_id}
            ''')
        op_treat_query = query_to_df(op_treat_sql, version)
        if not op_treat_query.empty:
            op_treat_query = column_separate(op_treat_query, 'treat_all', opcs)
            op_treat_query['source'] = 'Outpatients: OPCS4'
            treat_table = pd.concat([op_treat_query, treat_table])
        
        ecds_treat_sql = (f'''
            SELECT participant_id, seen_date as date, treatment_code_all as treat_all
            FROM ecds
            WHERE participant_id = {part_id}
            ''')
        ecds_treat_query = query_to_df(ecds_treat_sql, version)
        if not ecds_treat_query.empty:
            ecds_treat_query = column_separate(ecds_treat_query, 'treat_all', snomed)
            ecds_treat_query['source'] = 'Emergency care dataset: SNOMED CT'
            treat_table = pd.concat([ecds_treat_query, treat_table])
    
        treat_table['event'] = treat_table['treat_all'] + ": " + treat_table['meaning']
        return (treat_table[['participant_id', 'date', 'event', 'source']])

    def recruited (participant_id):
        type_sql = (f''' SELECT programme
            FROM key_columns
            WHERE participant_id = {participant_id}
            ''')
        type_query = query_to_df(type_sql, version)
        type = type_query.loc[0, 'programme']
        if (type == 'Rare Diseases'):
            rec_sql = (f''' SELECT participant_id, programme, participant_type, normalised_specific_disease as event, rare_disease_diagnosis_date as date
                FROM key_columns
                WHERE participant_id = {participant_id}
                ''')
            rec_query = query_to_df(rec_sql, version).drop_duplicates()
            rec_query['event'] = "Genomics England rare disease: " + rec_query['event']
            rec_query['source'] = "Recruited disease"
            return(rec_query[['participant_id', 'date', 'event', 'source']])
        elif (type == 'Cancer'):
            rec_sql = (f''' SELECT participant_id, programme, participant_type, cancer_disease_type as event, cancer_diagnosis_date as date
                FROM key_columns
                WHERE participant_id = {participant_id}
                ''')
            rec_query = query_to_df(rec_sql, version)
            rec_query['event'] = "Genomics England cancer: " + rec_query['event']
            rec_query['source'] = "Recruited disease"
            return(rec_query[['participant_id', 'date', 'event', 'source']])

    def hpo (participant_id):
        type_sql = (f''' SELECT participant_type
            FROM key_columns
            WHERE participant_id = {participant_id}
            ''')
        type_query = query_to_df(type_sql, version)
        type = type_query.loc[0, 'participant_type']
        if (type == 'rd_proband'):
            hpo_sql = (f''' SELECT participant_id, phenotype_report_date as date, normalised_hpo_id, normalised_hpo_term
                FROM rare_diseases_participant_phenotype
                WHERE participant_id = {participant_id}
                AND hpo_present = 'Yes'
                ''')
            hpo_query = query_to_df(hpo_sql, version)
            hpo_query['event'] = hpo_query['normalised_hpo_id'] + ": " + hpo_query['normalised_hpo_term']
            hpo_query['source'] = 'Rare diseases participant phenotype'
            return(hpo_query[['participant_id', 'date', 'event', 'source']])

    def cancer (participant_id):
        type_sql = (f''' SELECT participant_type
            FROM key_columns
            WHERE participant_id = {participant_id}
            ''')
        type_query = query_to_df(type_sql, version)
        type = type_query.loc[0, 'participant_type']    
        if (type == 'cancer_participant'):
            cancer_table = pd.DataFrame()
            staging_sql = (f'''
                SELECT
                  participant_id,
                  diagnosisdatebest as date,
                  grade,
                  component_tnm_t,
                  component_tnm_n,
                  component_tnm_m,
                  ajcc_stage,
                  dukes,
                  figo,
                  gleason_primary,
                  gleason_combined,
                  er_status,
                  pr_status,
                  her2_status
                FROM cancer_staging_consolidated
                WHERE participant_id = {participant_id}
                ''')
            staging_query = query_to_df(staging_sql, version)
            if not staging_query.empty:
                staging_query = staging_query.melt(id_vars=['participant_id', 'date'])
                staging_query = staging_query.dropna(subset = ['value'])
                staging_query['event'] = staging_query['variable'] + ": " + staging_query['value']
                staging_query = staging_query[['participant_id', 'date', 'event']]
                staging_query['source'] = "Cancer staging and grading"
                cancer_table = pd.concat([staging_query, cancer_table])
    
            avt_sql = (f'''
                SELECT
                    participant_id,
                    eventdate as date,
                    eventdesc,
                    opcs4_code,
                    opcs4_name
                FROM av_treatment
                WHERE participant_id = {participant_id}       
            ''')
            avt_query = query_to_df(avt_sql, version)
            if not avt_query.empty:
                avt_query['event'] = avt_query['eventdesc'] + (": " + avt_query['opcs4_code'] + ", " + avt_query['opcs4_name']).fillna('')   
                avt_query = avt_query[['participant_id', 'date', 'event']]
                avt_query['source'] = "AV tumour"
                cancer_table = pd.concat([avt_query, cancer_table])
    
            sact_sql = (f'''
                SELECT
                    participant_id,
                    analysis_group,
                    primary_diagnosis,
                    drug_group,
                    cycle_number,
                    programme_number,
                    start_date_of_cycle,
                    administration_date as date
                FROM sact
                WHERE participant_id = {participant_id} 
                ''')
            sact_query = query_to_df(sact_sql, version)
            if not sact_query.empty:
                sact_query['event'] = sact_query['analysis_group'] + ": " + sact_query['drug_group']  
                sact_query = sact_query[['participant_id', 'date', 'event']]
                sact_query['source'] = "Systemic anti-cancer therapy"
                cancer_table = pd.concat([sact_query, cancer_table])
    
            rtds_sql = (f'''
                SELECT
                    participant_id,
                    apptdate as date,
                    radiotherapyintent,
                    rttreatmentregion,
                    rttreatmentanatomicalsite,
                    primaryprocedureopcs
                FROM rtds
                WHERE participant_id = {participant_id} 
                ''')
            rtds_query = query_to_df(rtds_sql, version)
            if not rtds_query.empty:
                convert = pd.read_csv(opcs ,sep = '\t', dtype=str)
                rtds_query = pd.merge(rtds_query, convert, how = "left", left_on='primaryprocedureopcs', right_on = 'coding')
                intent = pd.DataFrame(
                    {'intent_code': [1, 2, 3],
                    'intent_term': ['Palliative', 'Anti-cancer', 'Other']}
                )
                rtds_query = pd.merge(rtds_query, intent, how = "left", left_on='radiotherapyintent', right_on = 'intent_code')
                region = pd.DataFrame(
                    {'region_code': ['P', 'R', 'PR', 'A', 'O', 'M'],
                    'region_term': ['Primary', 'Regional Nodes', 'Primary and Regional Nodes', 'Non-anatomically specific primary site', 'Prophylactic (to non-primary site)', 'Metastasis']}
                )
                rtds_query = pd.merge(rtds_query, region, how = "left", left_on='rttreatmentregion', right_on = 'region_code') 
                rtds_query['event'] = rtds_query['meaning'] + ": " + rtds_query['region_term'] + ", " + rtds_query['intent_term'] + (", " + rtds_query['rttreatmentanatomicalsite']).fillna('')
                rtds_query = rtds_query[['participant_id', 'date', 'event']]
                rtds_query['source'] = "Radiotherapy dataset"
                cancer_table = pd.concat([rtds_query, cancer_table])
                
            return(cancer_table)

    def all_clinical_table (participant_id):   
        table = pd.concat([diagnoses(participant_id), investigations(participant_id), treatments(participant_id), recruited(participant_id), cancer(participant_id), hpo(participant_id)])
        table['date'] = pd.to_datetime(table['date'])
        table = table.sort_values(by=['date'])
        return(table)

    # def clinical_graph(participant_id):
    #     input = all_clinical_table(participant_id).dropna()
    #     height = len(pd.unique(input['event']))/5
    #     input['event_trunc'] = input['event'].apply(lambda x: x[:20])
        
    #     plt.plot_date(input['date'], input['event_trunc'], xdate=True, ydate=False)
    #     plt.xticks(rotation=70)
    #     plt.figure(figsize=(10,height))
    #     groups = input.groupby('source')
    #     for name, group in groups:
    #         plt.plot(group.date, group.event_trunc, marker='o', linestyle='', markersize=3, label=name)
    #     plt.legend()
    #     plt.xlabel('Date of event')
    #     plt.ylabel('Event')
    #     plt.savefig(f'{participant_id}_graph.png', bbox_inches='tight')

    def html (participant_id):
        out = open(f"{participant_id}_output.html", "x")
        css = '''<html>
            <head>
            <style>
            body { font-family: Avenir, sans-serif; }
            td, th {
              border: 1px solid #ddd;
              padding: 8px;
            }
            table{
            overflow-x:auto;
            }
            tr:nth-child(even){background-color: #f2f2f2;}
            
            tr:hover {background-color: #ddd;}
            
            th {
              padding-top: 12px;
              padding-bottom: 12px;
              text-align: left;
              background-color: #df007d;
              color: white;
            }
            </style>
            </head>
            <body>'''
        out.write(css)
        out.write(about(participant_id))
        out.write("<h1>Family</h1>")
        out.write(family(participant_id))
        out.write("<h1>Genomics data</h1>")
        out.write(genomic(participant_id))    
        out.write("<h1>Clinical data</h1>")
        out.write(all_clinical_table(participant_id).to_html()) 
        # clinical_graph(participant_id)
        # out.write(f"<img src={participant_id}_graph.png>")
        out.write("</body>")
        out.close()
    html(participant_id)

if __name__ == "__main__":
    query()
