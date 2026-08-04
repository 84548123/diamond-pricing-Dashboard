import random
from datetime import datetime
from .base import DiamondAPIAdapter, DiamondRecord

class MockVDBAdapter(DiamondAPIAdapter):
    async def fetch_inventory(self) -> list[DiamondRecord]:
        random.seed(42)
        records = []
        
        shapes = ['ROUND']*40 + ['OVAL']*15 + ['CUSHION']*12 + ['EMERALD']*8 + ['PRINCESS']*7 + ['PEAR']*6 + ['RADIANT']*5 + ['MARQUISE']*3 + ['HEART']*2 + ['ASSCHER']*2
        colors = ['D']*5 + ['E']*8 + ['F']*12 + ['G']*18 + ['H']*20 + ['I']*15 + ['J']*12 + ['K']*5 + ['L']*3 + ['M']*2
        clarities = ['FL']*1 + ['IF']*3 + ['VVS1']*5 + ['VVS2']*8 + ['VS1']*15 + ['VS2']*18 + ['SI1']*20 + ['SI2']*15 + ['I1']*10 + ['I2']*3 + ['I3']*2
        cuts = ['EX']*40 + ['VG']*35 + ['GD']*20 + ['FR']*4 + ['PR']*1
        fluorescences = ['NON']*45 + ['FNT']*25 + ['MED']*15 + ['STG']*10 + ['VST']*5
        labs = ['GIA']*60 + ['IGI']*25 + ['HRD']*10 + ['AGS']*5
        countries = ['India']*40 + ['Belgium']*15 + ['Israel']*15 + ['USA']*10 + ['HongKong']*8 + ['UAE']*7 + ['Other']*5

        for i in range(500):
            shape = random.choice(shapes)
            color = random.choice(colors)
            clarity = random.choice(clarities)
            cut = random.choice(cuts)
            polish = random.choice(cuts)
            symmetry = random.choice(cuts)
            fluorescence = random.choice(fluorescences)
            lab = random.choice(labs)
            country = random.choice(countries)
            
            carat = round(random.uniform(0.30, 5.00), 2)
            
            base_price = 1000
            if color in ['D', 'E', 'F']: base_price *= 1.5
            elif color in ['G', 'H']: base_price *= 1.2
            
            if clarity in ['FL', 'IF', 'VVS1']: base_price *= 1.5
            elif clarity in ['VVS2', 'VS1']: base_price *= 1.3
            
            base_price *= max(1, carat ** 1.5)
            
            # Live fluctuation
            rand_time = datetime.utcnow().timestamp()
            fluctuation = random.Random(int(rand_time / 60)).uniform(-0.005, 0.005)
            price_per_carat = round(base_price * (1 + fluctuation), 2)
            
            price = round(price_per_carat * carat, 2)
            
            records.append(DiamondRecord(
                stone_id=f'VDB-{i+10000}',
                shape=shape,
                carat=carat,
                color=color,
                clarity=clarity,
                cut=cut,
                polish=polish,
                symmetry=symmetry,
                fluorescence=fluorescence,
                lab=lab,
                country=country,
                price=price,
                price_per_carat=price_per_carat,
                availability='AVAILABLE',
                updated_at=datetime.utcnow()
            ))
        return records

    async def health_check(self) -> bool:
        return True
