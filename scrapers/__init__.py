from scrapers.base import BaseScraper
from scrapers.orange import OrangeScraper
from scrapers.thales import ThalesScraper
from scrapers.cea import CEAScraper
from scrapers.inria import INRIAScraper
from scrapers.hellowork import HelloWorkScraper
from scrapers.doctorat_gouv import DoctoratGouvScraper
from scrapers.safran import SafranScraper
from scrapers.airbus import AirbusScraper
from scrapers.renault import RenaultScraper
from scrapers.edf import EDFScraper
from scrapers.aubertduval import AubertDuvalScraper
from scrapers.francetravail import FranceTravailScraper
from scrapers.abg import ABGScraper
from scrapers.stmicroelectronics import STMicroelectronicsScraper

ALL_SCRAPERS = [
    OrangeScraper,
    ThalesScraper,
    CEAScraper,
    INRIAScraper,
    DoctoratGouvScraper,
    SafranScraper,
    AirbusScraper,
    RenaultScraper,
    EDFScraper,
    AubertDuvalScraper,
    HelloWorkScraper,
    FranceTravailScraper,
    ABGScraper,
    STMicroelectronicsScraper,
]


