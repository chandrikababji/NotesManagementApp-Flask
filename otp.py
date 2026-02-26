import random
import string
def generate_otp():  #have to give this in app.py function name
    part1 = random.choice(string.ascii_uppercase)   
    part2 =random.choice(string.digits)    
    part3 = random.choice(string.ascii_lowercase)           
    part4 = random.choice(string.ascii_uppercase)  
    part5 = random.choice(string.digits)   
    part6 = random.choice(string.ascii_lowercase)            
    otp = part1 + part2 + part3 + part4 + part5 + part6 
    return otp
'''
#here i need to get 6 digit otp with 6 characters one is Capital,Number then small
import random
otp=""
for i in  range(2):  
   k=random.randint(65,90)
   j=chr(k)
   m=random.randint(1,9)
   d=str(m)
   l=random.randint(97,122)
   q=chr(l)
   otp+=j+d+q
print(otp)
'''
