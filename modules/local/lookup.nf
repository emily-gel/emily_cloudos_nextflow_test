process LOOKUP { 
    debug true

    publishDir path: "results"

    input: 
    val id

    output:
    path "${id}_output.html"

    script: 
    """
    lookup.py --participant_id ${id}
    """
}
