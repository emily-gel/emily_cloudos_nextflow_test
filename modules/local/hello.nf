process HELLO { 
    debug true

    input: 
    val greeting

    script: 
    """
    hello.py --greeting ${greeting}
    """
}
