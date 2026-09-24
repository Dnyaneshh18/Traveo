# What storage does passenger-app use?
# In passenger-app: const TOKEN_KEY = 'traveo.passenger.tokens';
# In passenger-tester: const TOKEN_KEY = 'traveo.passenger_tester.tokens';
# In driver-app: const TOKEN_KEY = 'traveo.driver.tokens';

# BUT on localhost:8081:
# If Dnyaneshwar logs in on browser A,
# and Yogesh logs in on browser A in another tab or same window,
# they overwrite the SAME localStorage key 'traveo.passenger.tokens'!
# Because both tabs are on http://localhost:8081!
