process LOOKUP { 
    debug true

    publishDir path: "results"

    input: 
    tuple \
        val id,
        path "ae_anatomical.tsv",
        path "ae_condition.tsv",
        path "ae_invest.tsv",
        path "ae_side.tsv",
        path "ae_treat.tsv",
        path "icd10.tsv",
        path "opcs.tsv",
        path "snomed.tsv"

    output:
    path "${id}_output.html"

    script: 
    """
    lookup.py --participant_id ${id}
    """
}
