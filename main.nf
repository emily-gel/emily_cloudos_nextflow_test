nextflow.enable.dsl=2

include { LOOKUP } from "./modules/local/lookup.nf"

workflow {

    Channel.value(params.id).set { ch_id }

    LOOKUP(ch_id)
}
