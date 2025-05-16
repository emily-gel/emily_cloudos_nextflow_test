process LOOKUP { 
    debug true

    publishDir path: "results"

    input: 
    val id

    output:
    path "${id}_output.txt"

    script: 
    """
    lookup.py --participant_id ${id}
    """
}
