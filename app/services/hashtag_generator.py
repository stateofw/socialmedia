"""
Intelligent Hashtag Generation System

Auto-generates optimized hashtags based on:
- Industry/service type
- City/location
- Content type
- Platform (Instagram vs LinkedIn vs Facebook)
- Trending topics (optional)
"""

from typing import List, Dict, Optional
from app.core.config import settings


class HashtagGenerator:
    """
    Intelligent hashtag generator for social media content.

    Features:
    - Industry-specific hashtags
    - Location-based hashtags
    - Content-type hashtags
    - Platform-optimized counts
    - Popularity balancing (high/medium/low competition)
    """

    # Hashtag templates by industry
    INDUSTRY_HASHTAGS = {
        "landscaping": [
            "Landscaping", "LawnCare", "YardWork", "GardenDesign", "OutdoorLiving",
            "Hardscaping", "TreeService", "LandscapeDesign", "GreenThumb", "YardMaintenance"
        ],
        "hvac": [
            "HVAC", "AirConditioning", "Heating", "AC", "Furnace", "HVACTech",
            "AirQuality", "HomeComfort", "HVACService", "ClimateControl"
        ],
        "roofing": [
            "Roofing", "RoofRepair", "RoofReplacement", "Roofer", "NewRoof",
            "RoofingContractor", "ResidentialRoofing", "RoofInspection", "ShingleRoof", "RoofMaintenance"
        ],
        "plumbing": [
            "Plumbing", "Plumber", "PlumbingRepair", "EmergencyPlumber", "DrainCleaning",
            "WaterHeater", "PipeRepair", "PlumbingService", "LeakRepair", "LocalPlumber"
        ],
        "electrical": [
            "Electrician", "ElectricalWork", "ElectricalRepair", "Wiring", "ElectricalService",
            "LightingInstall", "PanelUpgrade", "ElectricalContractor", "HomeElectrician", "CommercialElectrical"
        ],
        "cleaning": [
            "Cleaning", "HouseCleaning", "CleaningService", "CommercialCleaning", "DeepCleaning",
            "MaidService", "OfficeCleaning", "CleaningCompany", "ProfessionalCleaning", "EcoCleaning"
        ],
        "realestate": [
            "RealEstate", "Realtor", "HomeForSale", "HouseHunting", "PropertyForSale",
            "RealEstateAgent", "JustListed", "HomeBuyer", "RealEstateLife", "DreamHome"
        ],
        "restaurant": [
            "Restaurant", "FoodieLife", "LocalEats", "Foodie", "DineLocal",
            "RestaurantLife", "ChefLife", "FoodLover", "EatLocal", "FoodPorn"
        ],
        "fitness": [
            "Fitness", "Gym", "Workout", "FitnessMotivation", "PersonalTrainer",
            "GymLife", "FitnessJourney", "HealthyLifestyle", "FitFam", "TrainHard"
        ],
        "salon": [
            "Salon", "Hairstylist", "HairSalon", "Beauty", "Hairstyle",
            "BeautySalon", "HairGoals", "SalonLife", "HairTransformation", "BeautyTreatment"
        ],
    }

    # Content-type specific hashtags
    CONTENT_TYPE_HASHTAGS = {
        "before_after": ["BeforeAndAfter", "Transformation", "BeforeAfter", "MakeoverMonday"],
        "testimonial": ["ClientLove", "HappyCustomer", "Review", "Testimonial", "5StarService"],
        "offer": ["SpecialOffer", "Deal", "Discount", "Promotion", "LimitedTime"],
        "tip": ["ProTip", "ExpertAdvice", "Tips", "DidYouKnow", "HowTo"],
        "team_update": ["TeamWork", "MeetTheTeam", "BehindTheScenes", "OurTeam"],
        "project_showcase": ["ProjectShowcase", "WorkInProgress", "FeaturedWork", "Portfolio"],
        "seasonal": ["SpringTime", "SummerVibes", "FallSeason", "WinterReady"],
    }

    # Platform-specific hashtag counts
    PLATFORM_LIMITS = {
        "instagram": 30,  # Max 30, optimal 9-12
        "facebook": 3,    # Max unlimited, optimal 1-3
        "linkedin": 5,    # Max unlimited, optimal 3-5
        "twitter": 2,     # Max unlimited, optimal 1-2
        "tiktok": 5,      # Max unlimited, optimal 3-5
    }

    def generate_hashtags(
        self,
        industry: str,
        city: str,
        state: str,
        content_type: str,
        platform: str = "instagram",
        include_local: bool = True,
        include_branded: bool = False,
        business_name: Optional[str] = None,
    ) -> List[str]:
        """
        Generate optimized hashtags for a post.

        Args:
            industry: Business industry (e.g., "landscaping", "hvac")
            city: City name (e.g., "Brewster")
            state: State abbreviation (e.g., "NY")
            content_type: Type of content (e.g., "tip", "offer")
            platform: Target platform
            include_local: Include location-based hashtags
            include_branded: Include branded hashtags
            business_name: Business name (for branded hashtags)

        Returns:
            List of hashtags (with # prefix)
        """

        hashtags = []
        limit = self.PLATFORM_LIMITS.get(platform.lower(), 10)

        # 1. Industry hashtags (3-5)
        industry_tags = self._get_industry_hashtags(industry)
        hashtags.extend(industry_tags[:5])

        # 2. Location hashtags (2-3) if enabled
        if include_local:
            location_tags = self._get_location_hashtags(city, state, industry)
            hashtags.extend(location_tags[:3])

        # 3. Content-type hashtags (1-2)
        content_tags = self._get_content_type_hashtags(content_type)
        hashtags.extend(content_tags[:2])

        # 4. Branded hashtags (1) if enabled
        if include_branded and business_name:
            branded_tag = self._create_branded_hashtag(business_name)
            if branded_tag:
                hashtags.append(branded_tag)

        # 5. Generic engagement hashtags (1-2) for Instagram
        if platform.lower() == "instagram":
            hashtags.extend(["SmallBusiness", "LocalBusiness"][:2])

        # Remove duplicates while preserving order
        seen = set()
        unique_hashtags = []
        for tag in hashtags:
            tag_clean = tag.lower()
            if tag_clean not in seen:
                seen.add(tag_clean)
                unique_hashtags.append(tag)

        # Limit to platform maximum
        return unique_hashtags[:limit]

    def _get_industry_hashtags(self, industry: str) -> List[str]:
        """Get industry-specific hashtags."""
        industry_clean = industry.lower().replace(" ", "")

        # Get from predefined list
        tags = self.INDUSTRY_HASHTAGS.get(industry_clean, [])

        # Add generic industry tag if not in list
        if not tags:
            tags = [industry.replace(" ", "")]

        # Add hashtag prefix
        return [f"#{tag}" for tag in tags]

    def _get_location_hashtags(self, city: str, state: str, industry: str) -> List[str]:
        """
        Generate location-based hashtags.

        Examples:
        - #BrewsterNY
        - #NewYorkLandscaping
        - #BrewsterLandscaper
        """

        city_clean = city.replace(" ", "")
        state_clean = state.replace(" ", "")
        industry_clean = industry.replace(" ", "")

        tags = [
            f"#{city_clean}{state_clean}",  # #BrewsterNY
            f"#{state_clean}{industry_clean}",  # #NYLandscaping
            f"#{city_clean}{industry_clean}",  # #BrewsterLandscaper
            f"#Local{industry_clean}",  # #LocalLandscaper
        ]

        return tags

    def _get_content_type_hashtags(self, content_type: str) -> List[str]:
        """Get hashtags based on content type."""
        content_clean = content_type.lower().replace(" ", "_")
        tags = self.CONTENT_TYPE_HASHTAGS.get(content_clean, [])
        return [f"#{tag}" for tag in tags]

    def _create_branded_hashtag(self, business_name: str) -> Optional[str]:
        """Create a branded hashtag from business name."""
        # Remove common business suffixes
        name = business_name.replace(" LLC", "").replace(" Inc", "").replace(" Co", "")
        name = name.replace(".", "").replace(",", "").replace("&", "And")
        name_clean = "".join(name.split())  # Remove all spaces

        if len(name_clean) > 30:  # Too long for a hashtag
            return None

        return f"#{name_clean}"

    def get_hashtag_analytics(self, hashtags: List[str]) -> Dict:
        """
        Analyze hashtags for popularity/competition.

        Note: This is a basic implementation. For real analytics,
        integrate with Instagram Graph API or third-party tools.
        """

        # Basic popularity estimation based on hashtag characteristics
        high_competition = []
        medium_competition = []
        low_competition = []

        for tag in hashtags:
            tag_clean = tag.replace("#", "").lower()

            # High competition: generic, short, popular
            if len(tag_clean) <= 8 or tag_clean in ["fitness", "food", "business", "smallbusiness"]:
                high_competition.append(tag)
            # Low competition: very specific, long, branded
            elif len(tag_clean) > 20 or tag_clean.count("_") > 0:
                low_competition.append(tag)
            # Medium competition: everything else
            else:
                medium_competition.append(tag)

        return {
            "total": len(hashtags),
            "high_competition": high_competition,
            "medium_competition": medium_competition,
            "low_competition": low_competition,
            "balance": "good" if len(medium_competition) >= len(high_competition) else "improve",
        }

    def optimize_for_platform(
        self,
        hashtags: List[str],
        platform: str,
    ) -> List[str]:
        """
        Optimize hashtag list for specific platform.

        Different platforms have different best practices:
        - Instagram: 9-12 hashtags optimal (max 30)
        - Facebook: 1-3 hashtags (often performs better without)
        - LinkedIn: 3-5 professional hashtags
        - Twitter: 1-2 hashtags
        - TikTok: 3-5 hashtags
        """

        platform_lower = platform.lower()

        if platform_lower == "instagram":
            # Instagram: Use 9-12 for good engagement
            return hashtags[:12]

        elif platform_lower == "facebook":
            # Facebook: Keep minimal
            return hashtags[:2]

        elif platform_lower == "linkedin":
            # LinkedIn: Professional and relevant only
            # Filter out casual hashtags
            professional = [h for h in hashtags if "tip" in h.lower() or "service" in h.lower()]
            return (professional + hashtags)[:5]

        elif platform_lower == "twitter":
            # Twitter: 1-2 most relevant
            return hashtags[:2]

        elif platform_lower == "tiktok":
            # TikTok: 3-5 trending-focused
            return hashtags[:5]

        else:
            return hashtags[:10]


# Singleton instance
hashtag_generator = HashtagGenerator()
