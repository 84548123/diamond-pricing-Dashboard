import random
from datetime import datetime
from .base import DiamondAPIAdapter, DiamondRecord
from .mock_vdb import MockVDBAdapter

class MockDiamaxAdapter(DiamondAPIAdapter):
    async def fetch_inventory(self) -> list[DiamondRecord]:
        vdb_adapter = MockVDBAdapter()
        vdb_stones = await vdb_adapter.fetch_inventory()
        
        random.seed(43)
        records = []
        
        # 200 exact matches
        for i, vdb_stone in enumerate(vdb_stones[:200]):
            match_type_rand = random.random()
            if match_type_rand < 0.30:
                discount = random.uniform(0.10, 0.15)
            elif match_type_rand < 0.55:
                discount = random.uniform(0.05, 0.10)
            elif match_type_rand < 0.75:
                discount = random.uniform(0.03, 0.05)
            elif match_type_rand < 0.90:
                discount = random.uniform(0.0, 0.03)
            else:
                discount = random.uniform(-0.05, 0.0)
                
            rand_time = datetime.utcnow().timestamp()
            fluctuation = random.Random(int(rand_time / 60)).uniform(-0.005, 0.005)
            
            diamax_price = round(vdb_stone.price * (1 - discount) * (1 + fluctuation), 2)
            diamax_price_per_carat = round(diamax_price / vdb_stone.carat, 2)
            
            records.append(DiamondRecord(
                stone_id=f'DMX-M-{i+10000}',
                shape=vdb_stone.shape,
                carat=vdb_stone.carat,
                color=vdb_stone.color,
                clarity=vdb_stone.clarity,
                cut=vdb_stone.cut,
                polish=vdb_stone.polish,
                symmetry=vdb_stone.symmetry,
                fluorescence=vdb_stone.fluorescence,
                lab=vdb_stone.lab,
                country=vdb_stone.country,
                price=diamax_price,
                price_per_carat=diamax_price_per_carat,
                availability='AVAILABLE',
                updated_at=datetime.utcnow()
            ))
            
        # 300 unique diamax stones
        shapes = ['ROUND']*40 + ['OVAL']*15 + ['CUSHION']*12
        colors = ['D']*5 + ['E']*8 + ['F']*12 + ['G']*18
        clarities = ['FL']*1 + ['IF']*3 + ['VVS1']*5 + ['VVS2']*8
        cuts = ['EX']*40 + ['VG']*35
        fluorescences = ['NON']*45 + ['FNT']*25
        labs = ['GIA']*60 + ['IGI']*25
        countries = ['India']*40 + ['Belgium']*15
        
        for i in range(300):
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
            
            price_per_carat = round(random.uniform(2000, 15000), 2)
            price = round(price_per_carat * carat, 2)
            
            records.append(DiamondRecord(
                stone_id=f'DMX-U-{i+20000}',
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
