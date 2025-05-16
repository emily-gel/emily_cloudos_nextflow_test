process HELLO { 
    debug true

    publishDir path: "results"

    input: 
    val greeting

    output:
    path "${id}_output.txt"

    script: 
    """
    hello.py --id ${id}
    """
}
