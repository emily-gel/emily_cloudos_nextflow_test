include { HELLO } from "./modules/local/hello.nf"

workflow {
    ch_greeting = Channel.of(params.greeting) 
    
    HELLO(ch_greeting)
}
