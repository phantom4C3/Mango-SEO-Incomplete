




















Render preview snippets (meta_description or final_content).

In detail panel, show hybrid preview: iframe if published, innerHTML if not.

Leave all existing props/hooks in place for backward compatibility.





 

 



 






 
 
check if batch analysis is implemented 

also tell me in frontend should onclicked states remain in parent componenr or locally? consider rerenders due to extensive prop drilling and also if we fetch directly from component locally wont that affect multple user concyrrenycy?


check if we are redefining hooks locally instead of reusing those defined in store

can you check if each and every component is included in the final main editor?


in menu the button- leave this website - what is this actually used for does this mean we allow users to leave the current website and add another- wont that be an abuse of usage- should we allow users to have only one website for seo analysis

also should we make the menu dynamic - for onpageseo and different for ai blogwriting- what must be common and what must be conditional ?also shouldnt we change the seobot name- should we allow users to toggle aiblogwriting and onpageseo ?  

also what is on the left and right side of the maineditor- are they redundant ? 

what does the terminal actually do? show tasks progress via realtimelistener or something else ?

what is the autopilot function for ? also does the input only take website / yes/ no - shouldntwe only allow these - 

how is the website onboarded- is it directly sent to backend api for onbaording and scraping - should we use the api.ts helper for submit button in terminal ? 


also how can we make sure that each and every task is displayed on the terminal ? on the new line and not overriding the existing one ? should we display all tasks or just main ones- 

should we hide the input terminal for blogwriter since the user only has to select between the choices and not explicitly type anything ?

also why is there a publish blog button should we instead make it deploy changes for onpagesoe and publish blog for aiblogwriter or instead include it in the right side component- preview display ? 

also why is there a buy more button ? since we arent allowing users to buy more credits during an already existing plan - 

what do you think should be our pricing plan ? we are offering services that make up two saas together- we have features from both seobot and from ottoaiseo - can you check their pricing plans and tell me what exactly should be our strategy - should we keep one credit for one blog - also make sure to include credits for retries too and give me a solid plan, and tell me how to get rid of the buy more button in header 

also in main editor top header we are displaying tasks and articles both- should we get rid of them- or keep them and display all- tasks, articles and websites - seo analysed ?

shouldnt the right panel consist all the necessary task action buttons -  for both seo analysis and ai blog writing - shoul dthe panel be dynamic since we are acting according to task progress must it have any dynamuc butotn display etc - we already have separate components for both 


in menu what is the backlinks button for ? what purpose should it serve ? 

also can we fill settings modal one by one- how are we syncing the user settings in db? 

can we check working of the main editor- by connecting frontend and db and backend and getting rid of all placeholders ?

can you tell me what is calculated total tasks done or yet to be done?

also tell me since we dont have any login/signup page- will login button onclick handle google oauth redirect and login if we only have buttons for login/logout and signup? can we skip the login / singup page and instead allow users to access these functionalities via buttons only - how will the google oauth handle this and send the jwt token wherever necessary ? is itokay to only keep this - tell me how this jwt and oauth works ? will the jwt be sent to browser or anywhere else ? how will the jwt work ? 
 





