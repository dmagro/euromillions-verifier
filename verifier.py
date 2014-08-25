import httplib2
import xml.etree.ElementTree as ET


class Verifier(object):
	"""docstring for Verifier"""

	PREFIX = '{http://www.lottery.ie/resultsservice}'
	STAR_TYPE = "Star"
	STANDARD_TYPE = "Standard"
	NO_PRIZE = "no prize..."
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

	def has_prize(self):

		#Get xml from http request to the web services
		self.get_draw_results()

		#Verifies if the given date has a correct answer from the web services
		if not self.has_date_error():
			self.get_numbers_and_stars()
			self.compare_numbers__stars()
			self.prize = self.get_prize()
			self.response_to_user()
		else:
			print "Bad date..."

	def get_draw_results(self):

		date = self.string_date.replace(" ", "")

		url = "http://resultsservice.lottery.ie/ResultsService.asmx/GetResultsForDate?drawType=EuroMillions&drawDate=%s" % date
		h = httplib2.Http(".cache")
		(resp_headers, content) = h.request(url, "GET")

		self.xml_response = content

	def has_date_error(self):

		if self.xml_response == Verifier.DATE_LIMIT_ERROR or not self.has_info():
			return True

		return False

	def has_info(self):
		"""Verifies if the response xml has some info for error detection"""

		root = ET.fromstring(self.xml_response)
		#If has more than zero childs we have a good answer
		number_of_childs = len(list(root))

		if number_of_childs <= 0:
			return False

		return True

	def get_numbers_and_stars(self):
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

	def compare_numbers__stars(self):
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

	def get_prize(self):
		"""Verifies if a given combination has prize"""

		root = ET.fromstring(self.xml_response)

		for tier in root.iter(Verifier.PREFIX + 'Tier'):

			combination = tier.find(Verifier.PREFIX + 'Match').text
			if combination == self.result_combination:
				return tier.find(Verifier.PREFIX + 'Prize').text

		return Verifier.NO_PRIZE

	
	def response_to_user(self):

		if self.prize == Verifier.NO_PRIZE:
			print "You have " + Verifier.NO_PRIZE
		else:
			print "You won " + self.prize + " euros!!!"

			