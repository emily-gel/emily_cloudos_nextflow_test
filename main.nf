include { HELLO } from "./modules/local/hello.nf"

workflow {
    ch_greeting = Channel.of(params.greeting) 
    SETUP
    HELLO(ch_greeting)
}
