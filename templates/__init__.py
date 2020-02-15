from templates.oday_template import OdayParser
from templates.bmr_template import BMRParser
from templates.evolution_template import EvolutionParser
from templates.agora_template import AgoraParser
from templates.therealdeal_template import TheRealDealParser
from templates.abraxas_template import AbraxasParser
from templates.kiss_template import KissParser
from templates.andromeda_template import AndromedaParser
from templates.darknetheroes_template import DarkNetHeroesParser
from templates.exploit_template import ExploitParser
from templates.antichat_template import AntichatParser
from templates.breachforums_template import BreachForumsParser
from templates.greysec_template import GreySecParser
from templates.pandora_template import PandoraParser
from templates.thehub_template import TheHubParser
from templates.utopia_template import UtopiaParser
from templates.kickass_template import KickAssParser
from templates.darkode_template import DarkodeParser
from templates.greyroad_template import GreyRoadParser
from templates.sentrymba_template import SentryMBAParser
from templates.bitcointalk_template import BitCoinTalkParser
from templates.blackbank_template import BlackBankParser
from templates.bungee54_template import Bungee54Parser
from templates.cannabisroad_template import CannabisRoadParser
from templates.hydra_template import HydraParser
from templates.kingdom_template import KingdomParser
from templates.nucleus_template import NucleusParser
from templates.verified_template import VerifiedParser
from templates.wallstreet_template import WallStreetParser
from templates.galaxy3_template import Galaxy3Parser
from templates.galaxy1_template import Galaxy1Parser
from templates.silkroad1_template import SilkRoad1Parser
from templates.silkroad2_template import SilkRoad2Parser
from templates.lolzteam_template import LolzTeamParser
from templates.galaxy2_template import Galaxy2Parser
from templates.genesis_template import GenesisParser
from templates.hell_template import HellParser
from templates.nulled_to_template import NulledToParser
from templates.badkarma_template import BadKarmaParser
from templates.outlawmarket_template import OutLawMarketParser
from templates.alphabay_template import AlphaBayParser
from templates.sinister_template import SinisterParser
from templates.verified_carder_template import VerifiedCarderParser
from templates.carderme_template import CarderMeParser
from templates.ccc_mn_template import CCCMNParser
from templates.cracked_to_template import CrackedToParser
from templates.sky_fraud_template import SkyFraudParser
from templates.omerta_template import OmertaParser
from templates.dark_skies_template import DarkSkiesParser
from templates.procrd_template import ProcrdParser
from templates.blackbox_template import BlackBoxParser
from templates.v3rmillion_template import V3RMillionParser
from templates.silk_road3_template import SilkRoad3Parser
from templates.hiddenhand_template import HiddenHandParser
from templates.prvtzone_template import PrvtZoneParser
from templates.hackforums_template import HackForumsParser
from templates.darkwebs_template import DarkWebsParser
from templates.nulledbb_template import NulledBBParser
from templates.russian_carder_template import RussianCarderParser
from templates.blackhatworld_template import BlackHatWorldParser
from templates.thecc_template import TheCCParser
from templates.prtship_template import PrtShipParser
from templates.cardingschool_template import CardingSchoolParser
from templates.l33t_template import L33TParser
from templates.raidforums_template import RaidForumsParser
from templates.marviher_template import MarviherParser
from templates.lcpcc_template import LCPCCParser
from templates.runion_template import RUnionParser
from templates.raidforums_users_template import RaidForumsUserParser
from templates.xss_template import XSSParser
from templates.rstforums_template import RSTForumsParser
from templates.bhfio_template import BHFIOParser
from templates.crdclub_template import CrdClubParser
from templates.carderhub_template import CarderhubParser
from templates.primeforums_template import PrimeForumsParser
from templates.kriminala_template import KriminalaParser
from templates.leakportal_template import LeakPortalParser
from templates.hoxforum_template import HoxForumParser
from templates.scrapeboxforum_template import ScrapeBoxForumParser
from templates.fraudstercrew_template import FraudstercrewParser
from templates.crackx_template import CrackXParser
from templates.nulled_to_banlist import NulledToBanListParser
from templates.hashkiller_template import HashKillerParser
from templates.fuckav_template import FuckavParser
from templates.psbdmp_template import PsbdmpParser
from templates.youhack_template import YouHackParser
from templates.wwhclub_template import WwhclubParser
from templates.canadahq_template import CanadaHQParser
from templates.korovka_template import KorovkaParser
from templates.enclave_template import EnclaveParser
from templates.crimemarket_template import CrimeMarketParser
from templates.phreaker_template import PhreakerParser
from templates.prologic_template import ProLogicParser
from templates.dreammarket_template import DreamMarketParser
from templates.ogusers_template import OgUsersParser
from templates.ogusers_users_template import OgUsersUserParser
from templates.center_club_template import CenterClubParser
from templates.crackingpro_template import CrackingProParser
from templates.xrpchat_template import XrpChatParser
from templates.abusewith_template import AbuseWithParser
from templates.carding_team_template import CardingTeamParser
from templates.thebot_template import TheBOTParser
from templates.demonforums_template import DemonForumsParser
from templates.devilgroup_template import DevilGroupParser
from templates.bitshacking_template import BitsHackingParser
from templates.mashacker_template import MashackerParser
from templates.hackthissite_template import HackThisSiteParser
from templates.safeskyhacks_template import SafeskyhacksParser
from templates.skynetzone_template import SkynetzoneParser
from templates.rosanegra_template import RosanegraParser
from templates.envoy_template import EnvoyParser
from templates.devilteam_template import DevilteamParser
from templates.chknet_template import ChknetParser
from templates.torigon_template import TorigonParser
from templates.superbay_template import SuperBayParser
from templates.rutor_template import RutorParser
from templates.psxhax_template import PsxHaxParser
from templates.crackcommunity_template import CrackCommunityParser
from templates.freehack_template import FreeHackParser
from templates.phcracker_template import PhcrackerParser
from templates.cebulka_template import CebulkaParser


PARSER_MAP = {
    '0day': OdayParser,
    'bmr': BMRParser,
    'evolution': EvolutionParser,
    'agora': AgoraParser,
    'therealdeal': TheRealDealParser,
    'abraxas': AbraxasParser,
    'kiss': KissParser,
    'andromeda': AndromedaParser,
    'darknetheroes': DarkNetHeroesParser,
    'diabolus': DarkNetHeroesParser,
    'exploit': ExploitParser,
    'antichat': AntichatParser,
    'breachforums': BreachForumsParser,
    'greysec': GreySecParser,
    'pandora': PandoraParser,
    'thehub': TheHubParser,
    'utopia': UtopiaParser,
    'ka': KickAssParser,
    'darkode': DarkodeParser,
    'greyroad': GreyRoadParser,
    'sentrymba': SentryMBAParser,
    'bitcointalk': BitCoinTalkParser,
    'blackbank': BlackBankParser,
    'bungee54': Bungee54Parser,
    'cannabisroad': CannabisRoadParser,
    'hydra': HydraParser,
    'kingdom': KingdomParser,
    'nucleus': NucleusParser,
    'verified': VerifiedParser,
    'wallstreet': WallStreetParser,
    'galaxy3': Galaxy3Parser,
    'galaxy1': Galaxy1Parser,
    'silkroad1': SilkRoad1Parser,
    'silkroad2': SilkRoad2Parser,
    'lolzteam': LolzTeamParser,
    'galaxy2': Galaxy2Parser,
    'genesis': GenesisParser,
    'hell': HellParser,
    'nulled_to': NulledToParser,
    'badkarma': BadKarmaParser,
    'outlawmarket': OutLawMarketParser,
    'alphabay': AlphaBayParser,
    'sinister': SinisterParser,
    'verified_carder': VerifiedCarderParser,
    'carderme': CarderMeParser,
    'ccc_mn': CCCMNParser,
    'cracked_to': CrackedToParser,
    'sky_fraud': SkyFraudParser,
    'omerta': OmertaParser,
    'dark_skies': DarkSkiesParser,
    'procrd': ProcrdParser,
    'blackbox': BlackBoxParser,
    'v3rmillion': V3RMillionParser,
    'silkroad3': SilkRoad3Parser,
    'hiddenhand': HiddenHandParser,
    'prvtzone': PrvtZoneParser,
    'hackforums': HackForumsParser,
    'darkwebs': DarkWebsParser,
    'nulledbb': NulledBBParser,
    'russian_carder': RussianCarderParser,
    'blackhatworld': BlackHatWorldParser,
    'thecc': TheCCParser,
    'prtship': PrtShipParser,
    'carding_school': CardingSchoolParser,
    'l33t': L33TParser,
    'raidforums': RaidForumsParser,
    'marviher': MarviherParser,
    'lcpcc': LCPCCParser,
    'runion': RUnionParser,
    'raidforums_users': RaidForumsUserParser,
    'xss': XSSParser,
    'rstforums': RSTForumsParser,
    'bhfio': BHFIOParser,
    'crdclub': CrdClubParser,
    'carderhub': CarderhubParser,
    'primeforums': PrimeForumsParser,
    'kriminala': KriminalaParser,
    'leakportal': LeakPortalParser,
    'hoxforum': HoxForumParser,
    'scrapeboxforum': ScrapeBoxForumParser,
    'fraudstercrew': FraudstercrewParser,
    'crackx': CrackXParser,
    'nulled_to_banlist': NulledToBanListParser,
    'hashkiller': HashKillerParser,
    'fuckav': FuckavParser,
    'psbdmp': PsbdmpParser,
    'youhack': YouHackParser,
    'wwhclub': WwhclubParser,
    'canadahq': CanadaHQParser,
    'korovka': KorovkaParser,
    'enclave': EnclaveParser,
    'crimemarket': CrimeMarketParser,
    'phreaker': PhreakerParser,
    'prologic': ProLogicParser,
    'dreammarket': DreamMarketParser,
    'ogusers': OgUsersParser,
    'ogusers_users': OgUsersUserParser,
    'center_club': CenterClubParser,
    'crackingpro': CrackingProParser,
    'xrpchat': XrpChatParser,
    'abusewith': AbuseWithParser,
    'carding_team': CardingTeamParser,
    'thebot': TheBOTParser,
    'demonforums': DemonForumsParser,
    'devilgroup': DevilGroupParser,
    'bitshacking': BitsHackingParser,
    'mashacker': MashackerParser,
    'hackthissite': HackThisSiteParser,
    'safeskyhacks': SafeskyhacksParser,
    'skynetzone': SkynetzoneParser,
    'rosanegra': RosanegraParser,
    'envoy': EnvoyParser,
    'devilteam': DevilteamParser,
    'chknet': ChknetParser,
    'torigon': TorigonParser,
    'superbay': SuperBayParser,
    'rutor': RutorParser,
    'psxhax': PsxHaxParser,
    'crackcommunity': CrackCommunityParser,
    'freehack': FreeHackParser,
}
