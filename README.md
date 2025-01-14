# Auto Review Tools (v2)
This tool will help you automate the process of reviewing code
(version 2 adds caching (aioredis) and React frontend)
## Installation
You must have it installed Git and Docker
1. Clone the repository:
   ```bash
   git clone https://github.com/SergZels/CodeReviewAI-v2-.git
   cd  CodeReviewAI-v2-
2. Edit the .env file by entering your tokens for GitHub and OpenAI before running the next command.
3. ```bash
   docker compose up -d
  
5. Open your browser and navigate to:
   [http://127.0.0.1:7777/](http://127.0.0.1:7777/)

![img.png](img.png)

6. You can also use the API by sending `POST` requests to:
   [http://127.0.0.1:7777/review](http://127.0.0.1:7777/review)

   Here is the format of the request body:
   ```json
   {
     "assignment_description": "string",
     "github_repo_url": "https://github.com/SergZels/gameBot.git",
     "candidate_level": "Junior"
   }

  Part 2
  
Alright, since there are request limits for Git and OpenAI, real-time code review may not be feasible. An idea is to create a website with personal user accounts where they can submit input data and wait for responses later. For this task, we'll choose a microservices architecture. The site described above will be the first microservice, which will send this input data to RabbitMQ. A second microservice will receive this data at the necessary frequency (depending on Git and OpenAI limits), send requests, receive responses, process them, and store the results in JSON format in a database — either PostgreSQL or possibly MongoDB.

It’s also worth setting up notifications for users, informing them of completed results via messaging platforms or email. Upon an API request from the first microservice (or login to a personal account), responses will be retrieved from the database. Additionally, caching (Redis) should be enabled on the first microservice, as well as increase the number of --workers on the ASGI server and use balancing on the web server, for example, NGINX

