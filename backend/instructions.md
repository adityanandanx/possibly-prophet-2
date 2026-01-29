# BLOOM: AI Powered Instructional Content Creator
A heaven for teachers who want to create interactive AI generated slides fo the students to grasp the content more easily and help to engrain complex topics more easily.

## Backend Flow
- User (teacher) send a query request of certain types
    - Text Input: This is raw text data which is the context for the topic and that additionlly we get the Topic (optional field), Difficulty Level (Intermediate, Beginner, Advanced), Target Audience (Primary School, High School, University) and lastly a list text box of learning goals (optional field).
    - File Upload: This is a file that would be uploded to AWS knowlege base from where we will be able to access the context of this file and along with this we get Topic (optional field), Difficulty Level (Intermediate, Beginner, Advanced), Target Audience (Primary School, High School, University) and lastly a list text box of learning goals (optional field).
    - Web URL: This is the website URL, we need to scrape this page and give the usefull content as the context along with Topic (optional field), Difficulty Level (Intermediate, Beginner, Advanced), Target Audience (Primary School, High School, University) and lastly a list text box of learning goals (optional field).
- Now after this ingestion of context we use our "Pedagogical Agent" to expand the context in case of the raw text only as we want the file upload and web url context to be biased towards the content. So skip the "Pedagogical Agent" in case of web urls and file upload.
- Now time to generate the FDA or Formal Description of the animation using the next "FDA agent", this includes the content that will be shown during the manim animation. This is the generation of explicit rules of animation that would be converted into manim code.
- Now after the FDA has been generated using that we will be generating the actual manim code and that code will be rendered and saved as mp4 file and the slide timestamp json file in the S3 bucket.


## MOST IMPORTANT NOTES
- Do not use regex for output parsing use the strands SDK output parsers instead.