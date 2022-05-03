# Intro to Mathematical Optimization

## Problem Introduction

Today's workshop will be run by way of example. To help motivate what optimization is all about and how you can solve optimization problems, we will go to the garden. Deciding what to plant in a garden is a challenging problem for both backyard gardeners and large-scale farmers alike. The possibilities of what to grow seem endless, and the contstraints presented by reality never seem to stop popping up.

The Lynch family wants to decide what to plant in the garden. The goal is to grow fruits and vegetables that everyone will enjoy eating, while maximizing the yield and variety of the crops that are planted. Because they are expert planners, the garden plan will span the next three years. 

While coming up with an initial plan, several constraints presented themselves. Instead of shying away from the task, the Lynch family turned to optimization to help them in their hour of need. 

The following constraints will be covered in today's workshop:
- A tree blocks the sun for a good part of the day, making it difficult to grow sun-loving crops in parts of the garden. 
- Once a perennial is planted, it must stay in the bed to which it was assigned for the forseeable future. 
- Certain plants can't be planted in the same bed year-over-year without increasing the risk of certain soil-born diseases (we will use tomatoes as an example).
- A groundhog keeps digging under the fence and needs to be removed (not part of our optimization problem).

<br>
<br>

The problem we will walk through today has been simplified a bit. The goal here is to give us a starting point to talk about optimization without getting lost in the weeds of the problem. We simplify in the following ways:
- Decision variables are binary: whether or not to grow plant p in bed b during year t
- Only one crop can be planted in each bed

If you want to extend one or both of the approaches by introducing new constraints or objectives, here are a few interesting ways to complicate the problem:

- Switch from binary decision to grow plants in beds to an integer decision of the number of plants to grow in beds and add in spacing constraints. 
- Enable multiple plants to be grown in the same bed and promote companion planting.
- Build upon disease constraint to include other plants that should be avoided after planting problem plants.
- Force similar plants to be planted near each other.