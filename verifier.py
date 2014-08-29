import httplib2
import xml.etree.ElementTree as ET


class Verifier(object):
	"""docstring for Verifier"""

	PREFIX = '{http://www.lottery.ie/resultsservice}'
	STAR_TYPE = "Star"
	STANDARD_TYPE = "Standard"
	NO_PRIZE = "no prize..."
	STRING_RECOGNITION_ERROR = "Cannot convert"
	DATE_LIMIT_ERROR = "SqlDateTime overflow. Must be between 1/1/1753 12:00:00 AM and 12/31/9999 11:59:59 PM."

	
	def __init__(self, string_date, numbers, stars):
		self.string_date = string_date
		self.numbers = numbers
		self.stars = stars
		self.drawn_numbers = [] 
		self.drawn_stars = []
		self.result_combination = ""
		self.xml_response = ""
		self.prize = ""

		self.__get_info()

	@property
	def string_date(self):
	    return self._string_date

	@string_date.setter
	def string_date(self, date):
		if not date: raise Exception("Date cannot be empty.")
	    
		self.__get_draw_results(date)

		#if self.__has_date_error(): raise Exception("Bad date. Too old or not as 11 Aug 2014 form.")

		self._string_date = date

	@property
	def numbers(self):
		return self._numbers

	@numbers.setter
	def numbers(self, numbers_list):
		if not numbers_list: raise Exception("Numbers cannot be empty.")
		elif len(numbers_list) < 5 or len(numbers_list) > 5: raise Exception("Have to be exactly 5 numbers.")
		self._numbers = numbers_list

	@property
	def stars(self):
		return self._stars

	@stars.setter
	def stars(self, stars_list):
		if not stars_list: raise Exception("Numbers cannot be empty.")
		elif len(stars_list) < 2 or len(stars_list) > 2: raise Exception("Have to be exactly 2 star numbers.")
		self._stars = stars_list

	def __get_info(self):
		"""Gets the information for the class properties"""
		#Get xml from http request to the web services
		self.__get_draw_results()

		#Verifies if the given date has a correct answer from the web services
		if not self.__has_date_error():
			self.__get_numbers_and_stars()
			self.__compare_numbers__stars()
			self.prize = self.__get_prize()

	def __get_draw_results(self, string_date=[]):
		""" Ask to the web services for the results 
			of the draw in a certain date
		"""
		if not string_date:
			date = self.string_date.replace(" ", "")
		else:
			date = string_date.replace(" ", "")

		url = "http://resultsservice.lottery.ie/ResultsService.asmx/GetResultsForDate?drawType=EuroMillions&drawDate=%s" % date
		h = httplib2.Http(".cache")
		(resp_headers, content) = h.request(url, "GET")

		self.xml_response = content

	def __has_date_error(self):
		"""Verifies the correctness of the date"""

		date_limit_error = self.xml_response == Verifier.DATE_LIMIT_ERROR
		string_recognition_error =  Verifier.STRING_RECOGNITION_ERROR in self.xml_response

		if date_limit_error or string_recognition_error:
			raise Exception("Bad date. The string isn't in this form, ex: 11 Aug 2014.")
		elif not self.__has_info():
			raise Exception("Bad date. The date does not exist in the data base, too old.")

		return False

	def __has_info(self):
		"""Verifies if the response xml has some info for error detection"""

		root = ET.fromstring(self.xml_response)
		#If has more than zero childs we have a good answer
		number_of_childs = len(list(root))

		if number_of_childs <= 0:
			return False

		return True

	def __get_numbers_and_stars(self):
		"""Get the drawn numbers and stars from the xml response"""

		root = ET.fromstring(self.xml_response)

		numbers = []
		stars = []

		for numbers_tag in root.iter(Verifier.PREFIX + 'Numbers'):
			for draw_number_tag in numbers_tag.iterfind(Verifier.PREFIX + 'DrawNumber'):

				numberType = draw_number_tag.find(Verifier.PREFIX + 'Type').text
				number = int(draw_number_tag.find(Verifier.PREFIX + 'Number').text)

				if numberType == Verifier.STANDARD_TYPE:
					numbers.append(number)
				else:
					stars.append(number)

		self.drawn_numbers = numbers
		self.drawn_stars = stars

	def __compare_numbers__stars(self):
		"""Gets the combination of results from the comparison of numbers and stars"""

		number_of_correct_numbers = self.analyze_elements(self.numbers, self.drawn_numbers)
		number_of_correct_stars = self.analyze_elements(self.stars, self.drawn_stars)

		#You can have a prize just with numbers
		if number_of_correct_stars == 0:
			self.result_combination = str(number_of_correct_numbers)
		else:
			self.result_combination = str(number_of_correct_numbers) + "+" + str(number_of_correct_stars)

	@staticmethod
	def analyze_elements(user_elements, drawn_elements):
		"""This function verifies how many elements of the user list are in the draw list"""

		corrects = 0
		for element in user_elements:
			if element in drawn_elements:
				corrects += 1

		return corrects

	def __get_prize(self):
		"""Verifies if a given combination has prize"""

		root = ET.fromstring(self.xml_response)

		for tier in root.iter(Verifier.PREFIX + 'Tier'):

			combination = tier.find(Verifier.PREFIX + 'Match').text
			if combination == self.result_combination:
				return tier.find(Verifier.PREFIX + 'Prize').text

		return Verifier.NO_PRIZE

	def __response_to_user(self):

		if self.prize == Verifier.NO_PRIZE:
			print "You have " + Verifier.NO_PRIZE
		else:
			print "You won " + self.prize + " euros!!!"

	def has_prize(self):

		#Verifies if the given date has a correct answer from the web services
		if not self.__has_date_error():
			self.__response_to_user()
		else:
			print "Bad date..."
	
	def get_drawn_numbers(self):
		
		return self.drawn_numbers

	def get_drawn_stars(self):

		return self.drawn_stars

	def get_my_numbers(self):

		return self.numbers

	def get_my_stars(self):

		return self.stars

	def get_prize(self):

		return self.prize

	def get_combination(self):

		return self.result_combination