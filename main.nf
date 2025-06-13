nextflow.enable.dsl=2

include { LOOKUP } from "./modules/local/lookup.nf"

workflow {

    Channel.value(params.id).set { ch_id }
    ae_ana = Channel.fromPath("${projectDir}/resources/ae_anatomical.tsv")
    ae_con = Channel.fromPath("${projectDir}/resources/ae_condition.tsv")
    ae_inv = Channel.fromPath("${projectDir}/resources/ae_invest.tsv")
    ae_side = Channel.fromPath("${projectDir}/resources/ae_side.tsv")
    ae_tre = Channel.fromPath("${projectDir}/resources/ae_treat.tsv")
    icd10 = Channel.fromPath("${projectDir}/resources/icd10.tsv")
    opcs = Channel.fromPath("${projectDir}/resources/opcs.tsv")
    snomed = Channel.fromPath("${projectDir}/resources/snomed.tsv")

    LOOKUP(ch_id, ae_ana, ae_con, ae_inv, ae_side, ae_tre, icd10, opcs, snomed)
}
