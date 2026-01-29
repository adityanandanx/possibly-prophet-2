# BLOOM: AI Powered Instructional Content Creator
A heaven for teachers who want to create interactive AI generated slides fo the students to grasp the content more easily and help to engrain complex topics more easily.

## Frontend Flow
- User lands on the landing page.
- Now the user can directly go the dashboard.
- On the dasboard are their stats for how many lessons have they created and on which topics. 
- And continuing this the sidebar has the following elements
    - Text Input: User can enter some the context here in raw text format, like first when user comes on this page we will have a stepped structure where the user sees the content text box first and then they press next and then they see the options to enter Topic (optional field), Difficulty Level (Intermediate, Beginner, Advanced), Target Audience (Primary School, High School, University) and lastly a list text box of learning goals (optional field). Lastly a submit option.
    - File Upload: Here on the first step there will be option to upload the files (PDFs, Images, Visual Rich Documents). Then they press next and then they see the options to enter Topic (optional field), Difficulty Level (Intermediate, Beginner, Advanced), Target Audience (Primary School, High School, University) and lastly a list text box of learning goals (optional field). Lastly a submit option.
    - Web URL: This in the first step allows you to enter the URL for the website. Then they press next and then they see the options to enter Topic (optional field), Difficulty Level (Intermediate, Beginner, Advanced), Target Audience (Primary School, High School, University) and lastly a list text box of learning goals (optional field). Lastly a submit option.
- Sidebar will also have a "Your lessons" segment where the teachers can view their previous lessons.
- After they have submitted another page should appear that goes through what the backend is doing right now, which can be accessed through the endpoint. (Check `openapi.json`).
- Then after that call the manim code gen, rendering and S3 storing. (Check `openapi.json`).
- Now when you get the S3 link for the video. Then go to the page where we will be embedding the video using the S3 URL.

## Frontend Notes
- Fonts like Space Grotesk and PlayFair Display will be used.
- Make heavy use of graidents and little microinteractions.
- The landing page will have following sections.
    - The hero section with a flashy slogan which will have a dark blue and black gradient.
    - Then to explain our gimick we give a video of the working and some words to explain in the left. This will have a slant hard slant gradient.
    - Then we give cards of our top features.
    - Then we associate the team behind this (Aditya Nandan, Manish Gupta, Sparsh Singh, Mohd. Shahnawaz Khan).
    - Then some footer with links.
- The dashboard will be minimalistic but heavy with microinteractions.
- The charts in the dashboard will be made using ShadCN charts.
- The UI should follow the "Very rounded" aesthetic where most cards are rounded and buttons are pill shaped.
- The video player should be custom with icons from react-icons. 

## Frontend Tech Stack
- Next JS
- Axios for request
- Framer Motion
- React Icons
- ShadCN and TailWindCSS