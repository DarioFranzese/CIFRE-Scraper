# Task
Scrape the websites to find CIFRE PhD offers. The script will be run everyday so make sure to avoid duplicates and everytime there are new offers mark them as "new".
For each offer, extract:
- Title
- Company
- Description
- Link

I want you to develop a small GUI, most likely in browser, where i can manage these applications marking them as "not interested" (so they will be skipped in future) "applied already"  and refresh the interface.


In the future I will update the resources so have a structured file



# Sources


## PHD PLATFORM - https://app.doctorat.gouv.fr/
- use "CIFRE" as keyword to search and be sure it is included in the title or description of the filtered offers

## SAFRAN - https://www.safran-group.com/jobs?search=CIFRE&sort=relevance
- The last tag for the offer must be one of this: "IT", "Mathematics and algorithms", "Data", "Architecture and systems engineering"

## AIRBUS - https://ag.wd3.myworkdayjobs.com/en-US/Airbus?q=CIFRE

## RENAULT - https://alliancewd.wd3.myworkdayjobs.com/en-US/renault-group-careers?q=CIFRE

## CEA - https://www.emploi.cea.fr/offre-de-emploi/liste-offres.aspx
- use "these" as keyword and "CDD" as "Contrat" field

## EDF - https://www.edf.fr/en/edf-join-us/join-us/see-the-offers/our-offers?search[profil][34947]=34947

## ORANGE - https://orange.jobs/gb/en/search-results?keywords=phd
- check that "PhD" or "Thèse" is in the title

## THALES - https://careers.thalesgroup.com/global/en/search-results?keywords=CIFRE

## INRIA - https://jobs.inria.fr/public/classic/fr/offres?locale=fr
- use "CIFRE" as keyword

## HELLOWORK - https://www.hellowork.com/fr-fr/emploi/recherche.html?k=CIFRE&k_autocomplete=&l=&l_autocomplete=&st=relevance&msa=0&d=w

- skip the companies that are already present in this file

## LINKEDIN - https://www.linkedin.com/jobs/search/?currentJobId=4440509202&f_TPR=r604800&keywords=these%20cifre&origin=JOB_SEARCH_PAGE_JOB_FILTER
- be sure to search in France
- skip the companies that are already present in this file 
