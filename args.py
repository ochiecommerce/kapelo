from argparse import ArgumentParser

parser = ArgumentParser(
    prog='timebucks bot',
    usage='command [args]',
    description='cmd utility for timebucks automation'
)
parser.add_argument('-b',nargs='+',type=int,help='list of browsers to use')
parser.add_argument('-p',nargs='+',type=int,help='list of profiles to use')
parser.add_argument('-s',nargs='+',type=int,help='list of saved profile sessions to use')
parser.add_argument('-wd',help='working directory for the bot')

args = parser.parse_args()