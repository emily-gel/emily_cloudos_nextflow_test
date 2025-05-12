process HELLO { 
    debug true

    publishDir path: "results"

    input: 
    val greeting

    script: 
    """
    hello.py --greeting ${greeting}
    """
}
