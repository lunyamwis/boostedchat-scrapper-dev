def get_problems_and_solutions(calendar_availability, booking_system, ig_book_button):
    pp_need_new_client = "need new clients (styleseat)"
    pp_hidden_fees = "their booking system (styleseat) is charging their clients to book with them and additional hidden fees"
    pp_unjust_reviews = "they don't want to receive unjust reviews from cancelled bookings but their booking system (styleseat) allows those"
    pp_support = "StyleSeat customer support"

    naq_marketing_efficiency = "For a $40 haircut, the golden rule is to not spend more than $20 on acquiring that customer. Are you hitting that mark with your current marketing?"
    naq_hidden_fees = "Are you feeling the pinch with StyleSeat's client booking fees and other hidden expenses?"
    naq_unjust_reviews = "Heard StyleSeat doesn't filter out reviews from canceled appointments. Experienced any business attacks because of that?"
    naq_support = "How happy are you with StyleSeat's customer service? Can you easily chat with them when you need to?"

    sol_booksy_boost = "How happy are you with StyleSeat's customer service? Can you easily chat with them when you need to?"
    sol_hidden_fees = "Yikes, those hidden fees on StyleSeat are a bummer! How about a straightforward $30 monthly plan on Booksy with zero hidden charges? We're all about clarity and are available around the clock to chat if you ever need help. Thoughts?"
    sol_unjust_reviews = "Those StyleSeat reviews might get super frustrating! With Booksy, reviews are from verified customers—no more unwarranted negativity. And if you've got questions, we've got answers anytime. Interested?"
    sol_support = "Need help? We're here 24/7, by phone, email, or in-app. I'll also be here for you here on IG genuinely putting you first. Styleseat? Not so much."

    potential_problems = []
    assessment_questions = []
    solutions = []
    if booking_system == "Styleseat":
        if calendar_availability == "Empty Calendar":
            potential_problems = [pp_need_new_client, pp_hidden_fees, pp_unjust_reviews]
            assessment_questions = [naq_marketing_efficiency, naq_hidden_fees, naq_unjust_reviews]
            solutions = [sol_booksy_boost, sol_hidden_fees, sol_unjust_reviews]

        elif calendar_availability == "Some Availability":
            potential_problems = [pp_hidden_fees, pp_need_new_client, pp_unjust_reviews]
            assessment_questions = [naq_hidden_fees, naq_marketing_efficiency, naq_unjust_reviews]
            solutions = [sol_hidden_fees, sol_booksy_boost, sol_unjust_reviews]

        elif calendar_availability == "Fully Booked":
            potential_problems = [pp_support, pp_hidden_fees, pp_unjust_reviews]
            assessment_questions = [naq_support, naq_hidden_fees, naq_unjust_reviews]
            solutions = [sol_support, sol_hidden_fees, sol_unjust_reviews]
    return {
        "potential_problems": potential_problems,
        "assessment_questions": assessment_questions,
        "solutions": solutions
    }
