# Gyda

A tool to map short free text to phenotype and disease ontology terms.

Gyda aims to deal with several issues faced when trying to normalise short terms representing phenotypes or diseases from multiple sources. These short terms may be entered manually or automatically, but they may contain errors, use synonyms, use abbreviations or use different local spellings (e.g.: tumour versus tumor).

The steps to normalise any given term are:
1. Character normalisation, removal of any diacritics (e.g.: déjà vu => deja vu )
2. Tokenisation (e.g.: lymphoepithelioma-like carcinoma => "lymphoepithelioma", "like", "carcinoma")
3. Removal of stop words (e.g.: ocular albinism with sensorineural deafness => ocular albinism sensorineural deafness)
4. Stemming (e.g.: pigmentation => pigment)

Gyda supports any ontology in obo format, although we have used so far:
* Disease Ontology
* Human Phenotype Ontology
* OMIM
* SNOMED-CT (UK version)
* Gene Ontology

Target terms are evaluated against main names and synonyms in the provided ontologies using the Jaccard distance (0 represents a perfect match and 1 means no match at all).

![Alt text](docs/gyda.jpg?raw=true "Pipeline")

## Usage

`gyda_cli.py -h`
```
usage: gyda_cli.py [-h] [-p PHENOTYPE] [-i INFILE] [-o OUTFILE] [--hpo HPO]
                   [--do DO] [--omim OMIM] [--snomed SNOMED]
                   [--panelapp PANELAPP] [--threshold THRESHOLD]

Gyda phenotype mapper

optional arguments:
  -h, --help            show this help message and exit
  -p PHENOTYPE, --phenotype PHENOTYPE
                        a single input phenotype
  -i INFILE, --infile INFILE
                        a file containing a list of input phenotypes (one
                        phenotype per row)
  -o OUTFILE, --outfile OUTFILE
                        file name for csv with results (if not provided
                        results are printed to the standard output)
  --hpo HPO             location of hpo obo file
  --do DO               location of disease ontology obo file
  --omim OMIM           location of OMIM file
  --snomed SNOMED       location of SNOMEDCT file
  --panelapp PANELAPP   location of PanelApp file
  --threshold THRESHOLD
                        set the threshold for jaccard distance
```

Input a single phenotype and output in the standard output evaluated against HPO:
`gyda_cli.py -p "retinitis" --hpo hp.obo`

```
                  phenotype                 matched_term_name matched_term_id              matched_primary_name               score
1834   retinitis pigmentosa              Retinitis pigmentosa      HP:0000510                Rod-cone dystrophy                 0.0
13896  retinitis pigmentosa  Pericentral retinitis pigmentosa      HP:0007947  Pericentral retinitis pigmentosa  0.3333333333333333
13994  retinitis pigmentosa      Retinitis pigmentosa inversa      HP:0008035      Retinitis pigmentosa inversa  0.3333333333333333
[...]
```

Input a file with multiple phenotypes and output in a file evaluated against multiple ontologies:
`gyda_cli.py -i query_phenotypes.txt -o results.txt --hpo hp.obo --do doid-merged.obo --omim mimTitles.txt --snomed sct2_Description_Full-en_INT_20180131.txt`

## Libraries

* Natural Language Processing Toolkit (NLTK)
* Pronto to parse OBO ontology files

## Resources

The ontologies were downloaded from:
* HPO [http://human-phenotype-ontology.github.io/downloads.html](http://human-phenotype-ontology.github.io/downloads.html)
* DO [http://www.obofoundry.org/ontology/doid.html](http://www.obofoundry.org/ontology/doid.html)
* OMIM (requires registration)[https://omim.org/downloads/](https://omim.org/downloads/)
* SNOMED CT (UK version) [https://isd.digital.nhs.uk/trud3/user/guest/group/0/home](https://isd.digital.nhs.uk/trud3/user/guest/group/0/home)
