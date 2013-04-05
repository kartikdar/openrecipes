from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.selector import HtmlXPathSelector
from openrecipes.items import RecipeItem
from ..util import parse_iso_date


class AllrecipescrawlSpider(CrawlSpider):
    name = "allrecipes.com"
    allowed_domains = ["allrecipes.com"]
    start_urls = [
        # all of the recipes are linked from this page
        "http://allrecipes.com/recipes/ViewAll.aspx",
    ]

    # http://allrecipes.com/recipe/-applesauce-pumpkin-bread/detail.aspx
    # a tuple of Rules that are used to extract links from the HTML page
    rules = (
        # this rule has no callback, so these links will be followed and mined
        # for more URLs. This lets us page through the recipe archives
        Rule(SgmlLinkExtractor(allow=('/recipes/ViewAll.aspx?Page=\d+/'))),

        # this rule is for recipe posts themselves. The callback argument will
        # process the HTML on the page, extract the recipe information, and
        # return a RecipeItem object
        Rule(SgmlLinkExtractor(allow=('/recipe/.*/detail\.aspx')),
             callback='parse_item'),
    )

    def parse_item(self, response):
        hxs = HtmlXPathSelector(response)

        base_path = '//*[@itemtype="http://schema.org/Recipe"]'

        recipes_scopes = hxs.select(base_path)

        name_path = '//*[@itemprop="name"]/text()'
        description_path = '//*[@itemprop="description"]/text()'
        url_path = '//meta[@property="og:url"]/@content'
        image_path = '//*[@itemprop="image"]/@src'
        recipeYield_path = '*//*[@itemprop="recipeYield"]/text()'

        prepTime_path = '//*[@itemprop="prepTime"]'
        cookTime_path = '//*[@itemprop="cookTime"]'

        ingredients_path = '//*[@itemprop="ingredients"]'

        recipes = []
        for r_scope in recipes_scopes:
            item = RecipeItem()
            item['source'] = 'allrecipes'
            item['name'] = r_scope.select(name_path).extract()
            item['image'] = r_scope.select(image_path).extract()
            item['url'] = r_scope.select(url_path).extract()
            item['description'] = r_scope.select(description_path).extract()

            prepTime = r_scope.select(prepTime_path)
            item['prepTime'] = parse_iso_date(prepTime)

            cookTime = r_scope.select(cookTime_path)
            item['cookTime'] = parse_iso_date(cookTime)
            item['recipeYield'] = r_scope.select(recipeYield_path).extract()
            print item

            ingredient_scopes = r_scope.select(ingredients_path)
            ingredients = []
            for i_scope in ingredient_scopes:
                components = i_scope.select('node()/text()').extract()
                ingredients.append(' '.join(components))

            item['ingredients'] = ingredients

            recipes.append(item)

        return recipes
