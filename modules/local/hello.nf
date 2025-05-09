process HELLO { 
    debug true

    publishDir path: "results"

    input: 
    val greeting

    output:
    path("${greeting}.txt")

    script: 
    """
    hello.py --greeting ${greeting}
    """
}
