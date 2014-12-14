"""
goaffirmations.py

Scraper of http://health.goaffirmations.org/.

"Directory of Southeast Michigan healthcare
providers who affirm lesbian, gay, bisexual,
and transgender people. Filter our list of
providers by choosing criteria below."

"""
import requests
from scraper import Scraper
from radrecord import rad_record


class GoAffirmationsScraper(Scraper):
    """
    Scraper for the Affirmations Network in Michigan.
    This website is statically generated and then made interactive
    with Javascript. Their source code is hosted on Github and we
    can just take their data from the repository instead of parsing
    html.

    This is what a record looks like from this data set:

    {"id":"35",
     "providername":"Allen E. Kash, DC",
     "agencyname":"Madison Heights Chiropractic",
     "type":["Chiropractor"],
     "orientation":["Heterosexual"],
     "sexgenderidentity":["Male"],
     "race":["White"],
     "languages":["English","Spanish"],
     "county":["Oakland"],
     "streetaddress":"28107 John R. Road",
     "city":"Madison Heights",
     "state":"MI",
     "zip":"48071",
     "officehours":"Monday, Wednesday, Friday 9-12:30 & 2:30-7\nTuesday 2:30-7\nSaturday 8-12",
     "nearbus":true,
     "nearbybuslines":["SMART 495"],
     "mailingstreetaddress":"",
     "mailingcity":"",
     "mailingstate":"",
     "mailingzip":"",
     "phone":"(248) 542-3492",
     "website":"www.madisonheightschiro.com",
     "email":"madhgtschiro@aol.com",
     "insurancesaccepted":"accepts Medicare, Medicaid, Great Lakes Health Plan, BCBS, PPOM, others that cover chiropractic care",
     "lowincome":true,
     "specialties":[],
     "trainings":"Neck and back problems; Headaches; Arm or leg pain; Disc degeneration",
     "completedculturalcompetencytraining":false,
     "affirmationstrainings":[],
     "comments":"",
     "rowNumber":1}

    """

    PROVIDERS_RAW = \
        'https://raw.githubusercontent.com/workdept/affirmations-referral-network/master/src/data/providers.json'

    def __init__(self):
        super(GoAffirmationsScraper, self).__init__(source='Michigan\'s Affirmations Referral Network')

    def scrape(self):

        resp = requests.get(self.PROVIDERS_RAW)

        if resp.status_code == requests.codes.ok:
            data = resp.json()

            return map(lambda r: rad_record(name=r['providername'],
                                     organization=r['agencyname'],
                                     street=r['streetaddress'],
                                     city=r['city'],
                                     country='U.S.A',
                                     zipcode=r['zip'],
                                     email=r['email'],
                                     phone=r['phone'],
                                     url=r['website'],
                                     source=self.source,
                                     category_names=r['type'],
                                     hours=r['officehours']),
                       data)

        else:
            print('Failed to scrape {0}'.format(self.source))

x = GoAffirmationsScraper()
x.run()
