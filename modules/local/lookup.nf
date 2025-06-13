process LOOKUP { 
    debug true

    publishDir path: "results"

    input: 
    tuple val(id), path(ae_ana), path(ae_con), path(ae_inv), path(ae_side), path(ae_tre), path(icd10), path(opcs), path(snomed)

    output:
    path "${id}_output.html"

    script: 
    """
    lookup.py --participant_id ${id} --ae_ana ${ae_ana} --ae_con ${ae_con} --ae_inv ${ae_inv} --ae_side ${ae_side} --ae_tre ${ae_tre} --icd10 ${icd10} --opcs ${opcs} --snomed ${snomed}
    """
}
