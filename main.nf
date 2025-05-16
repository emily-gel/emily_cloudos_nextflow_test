include { LOOKUP } from "./modules/local/lookup.nf"

workflow {
    ch_id = Channel.of(params.id) 

    LOOKUP(ch_id)
}
