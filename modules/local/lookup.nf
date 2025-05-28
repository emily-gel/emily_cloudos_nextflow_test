process LOOKUP { 
    debug true

    publishDir path: "results"

    input: 
    val id

    output:
    path "${id}_output.tsv"

    script: 
    """
    lookup.py --participant_id ${id}
    """
}
