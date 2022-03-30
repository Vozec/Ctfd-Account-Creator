import re
import requests
import random
import json
import os
import argparse

def header():
	print(r"""
   ______________________     ______                __            
  / ____/_  __/ ____/ __ \   / ____/_______  ____ _/ /_____  _____
 / /     / / / /_  / / / /  / /   / ___/ _ \/ __ `/ __/ __ \/ ___/
/ /___  / / / __/ / /_/ /  / /___/ /  /  __/ /_/ / /_/ /_/ / /    
\____/ /_/ /_/   /_____/   \____/_/   \___/\__,_/\__/\____/_/     
                                                                  
""")

def Check_Ctfd(session,url):
	try:
		if('' in session.get(url).text):
			return True
		return False
	except Exception as ex:
		print(' [+] Error during ctfd check : %s'%str(ex))
		return False


def CheckTeam_Exist(url,req,user):
	try:
		resp = req.get(url+'/teams?field=name&q=%s'%user['team']).text
		all_ = list(zip(*list(re.findall(r'<a href="/teams/(.*?)">(.*?)</a>',resp))))
		if(len(all_) != 0):
			if(user["team"].lower() in list((map(lambda x: x.lower(), all_[1])))):
				return True		
		return False
	except Exception as ex:
		print(" [+] Error to check if team exist : %s"%str(ex))
		return False


def CheckUser_Exist(url,req,user):
	try:
		resp = req.get(url+'/users?field=name&q=%s'%user['pseudo']).text.replace("\n","").replace("\t","")
		all_ = list(zip(*list(re.findall(r'<a href="/users/(.*?)">(.*?)</a>',resp))))
		if(len(all_) != 0):
			if(user["pseudo"].lower() in list((map(lambda x: x.lower(), all_[1])))):
				return True		
		return False
	except Exception as ex:
		print(" [+] Error to check if user exist : %s"%str(ex))
		return False


def CheckTeam_User(url,req,user):
	try:
		verif = req.get(url+'/api/v1/users/me').text
		if(type(json.loads(verif)["data"]["team_id"]) == int):
			return True
		return False
	except Exception as ex:
		print(" [+] Error to check user account : %s"%str(ex))
		return False


def Join_Team(url,req,user):
	try:
		html = req.get(url + "/teams/join").text
		token = re.search(r"csrfNonce': \"(.*?)\",",html).group(1);	# Get token csrf
		post = {"name":user["team"],"password":user["team_password"],"_submit":"Join","nonce":token}	# Post Data
		resp = req.post(url+'/teams/join',post).text	# Create Team
		return CheckTeam_User(url,req,user)
	except Exception as ex:		
		print(" [+] Error to join the team : %s"%str(ex))
		return False


def Create_Team(url,req,user):
	try:
		html = req.get(url + "/teams/new").text
		token = re.search(r"csrfNonce': \"(.*?)\",",html).group(1);	# Get token csrf
		post = {"name":user["team"],"password":user["team_password"],"_submit":"Create","nonce":token}	# Post Data
		resp = req.post(url+'/teams/new',post).text	# Create Team
		return CheckTeam_User(url,req,user)
	except Exception as ex:
		print(" [+] Error during team creation : %s"%str(ex))
		return False
  

def Register_Account(req,user,url):
	try:
		html = req.get(url + "/register").text 		 # Get html page		
		token = re.search(r"csrfNonce': \"(.*?)\",",html).group(1);# Get token
		rep = req.post(url+'/register',{"name":user['pseudo'],"email":user['email'],"password":user['password'],"nonce":token,"_submit":"Submit"}).text# Post request
		if('Logout' in rep):
			return True
		return False
	except Exception as ex:
		print(" [+] Error during registration : %s"%str(ex))
		return False


def Login_Account(req,user,args):
	try:
		if(args.verbose):
			print("\n [+] Checking if user '%s' exist"%user["pseudo"])

		if(CheckUser_Exist(args.url,req,user)):
			# Login to account			
			if(args.verbose):
				print(" [+] Logging to %s Account"%user["pseudo"])
			html = req.get(args.url + "/login").text 		 # Get html page		
			token = re.search(r"csrfNonce': \"(.*?)\",",html).group(1);# Get token
			rep = req.post(args.url+'/login',{"name":user['pseudo'],"password":user['password'],"_submit":"Submit","nonce":token}).text# Post request
			if('Logout' in rep):
				return True
			return False
		else:
			# Creating account
			if(args.verbose):
				print(" [+] Creating Account for %s"%user["pseudo"])
			return Register_Account(req,user,args.url)
		
	except Exception as ex:
		print(" [+] Error during login : %s"%str(ex))
		return False


def Ctfd_Register(req,user,args):
	try:
		# Login/Create Account
		if(Login_Account(req,user,args)):

			if(args.verbose):
				print(" [+] Logged to the account")
				print(" [+] Checking if team '%s' exist"%user["team"])

			# Check if team exist
			in_team = False
			if not CheckTeam_User(args.url,req,user):
				if(CheckTeam_Exist(args.url,req,user)):
					# Join Team
					if(args.verbose):
						print(" [+] Joining the team '%s'"%user["team"])
					in_team = Join_Team(args.url,req,user)
				else:
					# Create Team
					if(args.verbose):
						print(" [+] Creating the team '%s'"%user["team"])
					in_team = Create_Team(args.url,req,user)

				if(args.verbose and not in_team):
					print(" [+] Error in the team process")

			else:
				print(" [+] User %s is already in a team "%user["pseudo"])


			return True,in_team
		else:
			return False,False
	except Exception as ex:
		print(" [+] Error during registration : %s"%str(ex))
		return False,False

def parse_args():
	parser = argparse.ArgumentParser(add_help=True, description='This tool is used to automatically create accounts on CTFD platform.')
	parser.add_argument("-u", "--url", dest="url", required=True, help="Url of the Ctfd.")
	parser.add_argument("-c", "--config", dest="config_path", required=True, help="Path of the config (*.json).")
	parser.add_argument("-v", "--verbose", dest="verbose", action="store_true", default=False, help="Use verbose mode.")
	parser.add_argument("-q", "--quit", dest="quit", action="store_true", default=False, help="Use quit mode.")
	parser.add_argument("-d", "--discord", dest="discord", action="store_true", default=False, help="Displays the account created in a Discord Message template")
	args = parser.parse_args()
	return args


def main():

	## INIT
	args = parse_args()
	if(not args.quit):
		header()
	os.chdir(os.path.abspath(os.getcwd()))
	session = requests.session()

	## SANITIZE URL
	if not args.url.startswith("http://") and not args.url.startswith("https://"):
		args.url = "https://" + args.url	
	args.target = args.url.rstrip('/')

	## CHECK IF VALID INPUT
	if(not Check_Ctfd(session,args.url)):
		print(" [+] Please provide a valid url !")
		return
	elif(not os.path.exists(args.config_path)):
		print(" [+] Please provide a valid path , config not found : %s "%(args.config_path))
		return
	else:

		## Load config file
		config = json.loads(open(args.config_path, "r").read())

		## Create account for all users
		for user in config["users"]:

			session.cookies.clear()

			# If Mail/Password Empty in Json
			if(user[1] == ""):
				user[1] = "%s@tempmail.com"%(''.join(random.choice("abcdefghijklmnopqrstuvwxyz") for i in range(12)))
			if(user[2] == ""):
				user[2] = ''.join(random.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+-*:/;.") for i in range(12))

			data = {
				"pseudo":user[0],
				"email":user[1],
				"password":user[2],
				"team":config["team"],
				"team_password":config["teampwd"],
				}

			succeed,in_team = Ctfd_Register(session,data,args)
			
			
			if(succeed):
				if(not args.discord):
					print(f" [+] User successfully created !\n")
				else:
					print("```")
				print(f"    \t- {'Name:':<12}\t{data['pseudo']:>12}")
				print(f"    \t- {'Password:':<12}\t{data['password']:>12}")
				print(f"    \t- {'Email:':<12}\t{data['email']:>12}")
				if(in_team):
					print(f"    \t- {'Team:':<12}\t{data['team']:>12}")
					print(f"    \t- {'Team Pass:':<12}\t{data['team_password']:>12}")
				if(args.discord):
					print("```")		
			else:
				print("\n [+] Failed To Login/Create the account %s"%user[0])





if __name__ == '__main__': 
	main()