from django.core.management.base import BaseCommand
from tickets.models import Game


class Command(BaseCommand):
    help = 'Populate database with sample pinball machines for development'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing games before adding sample data',
        )

    def handle(self, *args, **options):
        if options['clear']:
            count = Game.objects.count()
            Game.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(f'Deleted {count} existing game(s)')
            )

        # Sample pinball machines from museum inventory
        sample_games = [
            {
                "name": "Ballyhoo",
                "manufacturer": "Bally",
                "month": 1,
                "year": 1932,
                "type": Game.TYPE_PM,
                "scoring": "manual",
                "flipper_count": "0",
                "status": Game.STATUS_GOOD,
                "ipdb_url": "https://www.ipdb.org/machine.cgi?id=4817",
            },
            {
                "name": "Carom",
                "manufacturer": "Bally",
                "month": 1,
                "year": 1937,
                "type": Game.TYPE_EM,
                "scoring": "totalizer",
                "flipper_count": "0",
                "status": Game.STATUS_UNKNOWN,
                "ipdb_url": "https://www.ipdb.org/machine.cgi?id=458",
            },
            {
                "name": "Trade Winds",
                "manufacturer": "United",
                "month": 3,
                "year": 1945,
                "type": Game.TYPE_EM,
                "scoring": "lights",
                "status": Game.STATUS_FIXING,
                "ipdb_url": "https://www.ipdb.org/machine.cgi?id=2620",
            },
            {
                "name": "Baseball",
                "manufacturer": "Chicago Coin",
                "month": 10,
                "year": 1947,
                "type": Game.TYPE_EM,
                "scoring": "lights",
                "flipper_count": "2",
                "status": Game.STATUS_BROKEN,
                "ipdb_url": "https://www.ipdb.org/machine.cgi?id=189",
            },
            {
                "name": "Derby Day",
                "manufacturer": "Gottlieb",
                "month": 4,
                "year": 1956,
                "type": Game.TYPE_EM,
                "scoring": "lights",
                "flipper_count": "2",
                "status": Game.STATUS_GOOD,
                "ipdb_url": "https://www.ipdb.org/machine.cgi?id=664",
            },
            {
                "name": "Roto Pool",
                "manufacturer": "Gottlieb",
                "month": 7,
                "year": 1958,
                "type": Game.TYPE_EM,
                "scoring": "lights",
                "flipper_count": "2",
                "status": Game.STATUS_GOOD,
                "ipdb_url": "https://www.ipdb.org/machine.cgi?id=2022",
            },
            {
                "name": "Teacher's Pet",
                "manufacturer": "Williams",
                "month": 12,
                "year": 1965,
                "type": Game.TYPE_EM,
                "scoring": "reels",
                "flipper_count": "2",
                "pinside_rating": 8.34,
                "status": Game.STATUS_GOOD,
                "ipdb_url": "https://www.ipdb.org/machine.cgi?id=2506",
            },
            {
                "name": "Hokus Pokus",
                "manufacturer": "Bally",
                "month": 3,
                "year": 1976,
                "type": Game.TYPE_EM,
                "scoring": "reels",
                "flipper_count": "2",
                "pinside_rating": 7.94,
                "status": Game.STATUS_GOOD,
                "ipdb_url": "https://www.ipdb.org/machine.cgi?id=1206",
            },
            {
                "name": "Star Trip",
                "manufacturer": "GamePlan",
                "month": 4,
                "year": 1979,
                "type": Game.TYPE_SS,
                "scoring": "7-segment",
                "system": "MPU_1",
                "flipper_count": "2",
                "status": Game.STATUS_GOOD,
                "ipdb_url": "https://www.ipdb.org/machine.cgi?id=3605",
            },
            {
                "name": "Star Trek",
                "manufacturer": "Bally",
                "month": 4,
                "year": 1979,
                "type": Game.TYPE_SS,
                "scoring": "7-segment",
                "system": "Bally MPU AS-2518-35",
                "flipper_count": "2",
                "pinside_rating": 6.76,
                "status": Game.STATUS_FIXING,
                "ipdb_url": "https://www.ipdb.org/machine.cgi?id=2355",
            },
            {
                "name": "The Hulk",
                "manufacturer": "Gottlieb",
                "month": 10,
                "year": 1979,
                "type": Game.TYPE_SS,
                "scoring": "7-segment",
                "system": "System 1",
                "flipper_count": "2",
                "status": Game.STATUS_GOOD,
                "ipdb_url": "https://www.ipdb.org/machine.cgi?id=1266",
            },
            {
                "name": "Gorgar",
                "manufacturer": "Williams",
                "month": 12,
                "year": 1979,
                "type": Game.TYPE_SS,
                "scoring": "7-segment",
                "system": "System 6",
                "flipper_count": "2",
                "pinside_rating": 7.56,
                "status": Game.STATUS_FIXING,
                "ipdb_url": "https://www.ipdb.org/machine.cgi?id=1062",
            },
            {
                "name": "Blackout",
                "manufacturer": "Williams",
                "month": 6,
                "year": 1980,
                "type": Game.TYPE_SS,
                "scoring": "7-segment",
                "system": "System 6",
                "flipper_count": "2",
                "pinside_rating": 7.70,
                "status": Game.STATUS_FIXING,
                "ipdb_url": "https://www.ipdb.org/machine.cgi?id=317",
            },
            {
                "name": "Hyperball",
                "manufacturer": "Williams",
                "month": 12,
                "year": 1981,
                "type": Game.TYPE_SS,
                "scoring": "alphanumeric",
                "system": "System 7",
                "flipper_count": "0",
                "status": Game.STATUS_GOOD,
                "ipdb_url": "https://www.ipdb.org/machine.cgi?id=3169",
            },
            {
                "name": "Eight Ball Deluxe Limited Edition",
                "manufacturer": "Bally",
                "month": 8,
                "year": 1982,
                "type": Game.TYPE_SS,
                "scoring": "7-segment",
                "system": "Bally MPU AS-2518-35",
                "flipper_count": "3",
                "pinside_rating": 8.06,
                "status": Game.STATUS_GOOD,
                "ipdb_url": "https://www.ipdb.org/machine.cgi?id=763",
            },
            {
                "name": "The Getaway: High Speed II",
                "manufacturer": "Williams",
                "month": 2,
                "year": 1992,
                "type": Game.TYPE_SS,
                "scoring": "DMD",
                "system": "Fliptronics 2?",
                "flipper_count": "3",
                "pinside_rating": 8.14,
                "status": Game.STATUS_GOOD,
                "ipdb_url": "https://www.ipdb.org/machine.cgi?id=1000",
            },
            {
                "name": "The Addams Family",
                "manufacturer": "Williams",
                "month": 3,
                "year": 1992,
                "type": Game.TYPE_SS,
                "scoring": "DMD",
                "system": "Fliptronics 1?",
                "flipper_count": "4",
                "pinside_rating": 8.56,
                "status": Game.STATUS_GOOD,
                "ipdb_url": "https://www.ipdb.org/machine.cgi?id=20",
            },
            {
                "name": "Godzilla (Premium)",
                "manufacturer": "Stern",
                "month": 10,
                "year": 2021,
                "type": Game.TYPE_SS,
                "scoring": "video",
                "system": "Spike 2",
                "flipper_count": "3",
                "pinside_rating": 9.19,
                "status": Game.STATUS_GOOD,
                "ipdb_url": "https://www.ipdb.org/machine.cgi?id=6842",
            },
        ]

        created_count = 0
        existing_count = 0

        for game_data in sample_games:
            game, created = Game.objects.get_or_create(
                name=game_data["name"],
                defaults=game_data
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created: {game.name} ({game.year} {game.manufacturer})')
                )
            else:
                existing_count += 1
                self.stdout.write(
                    f'  Already exists: {game.name}'
                )

        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Summary: {created_count} created, {existing_count} already existed'
            )
        )
