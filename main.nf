include { HELLO } from "./modules/local/hello.nf"

workflow {
    ch_id = Channel.of(params.id) 
    HELLO(ch_id)
}
