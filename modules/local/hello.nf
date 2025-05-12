process HELLO { 
    debug true

    publishDir path: "results"

    input: 
    val greeting

    output:
    path "${greeting}_output.txt"

    script: 
    """
    hello.py --greeting ${greeting}
    """
}
