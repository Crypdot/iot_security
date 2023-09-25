---
name: "First meeting, project scope" 
course_title: "Monialainen Innovaatioprojekti"
course_ID: "XX00DZ39-3061"
date: "06-09-2023"
participants: Alex, Amir, Ian, Kalle, Saku
tags: iot, inno, MeetingNotes
---

# Meeting Notes
The project has a number of parts: 
- The project covers a medical device to be remade. It should have MQTT broadcasting capabilities. It has a screen on it so it is possible to build a small UI to better facilitate interaction.
	- Rebuild it. Technologies used, preferably: Python, RaspberryPi, Golang.
	- Extract data from it, and send it over using MQTT.
	- Send data to the [attestation engine](https://github.com/nokia/AttestationEngine).
	- Blockhain (Optional, can ask Ian for further information if we want to go through with this.)
	- Completion should take roughly 2-3 months.
	- Visualization using Influx or Grafana.
- Ian has some example code we can work off of to further assist learning.
- Pi, arduino, sensors communicating using MQTT and a server component.

- We can get remote access, through SSH, but it's a bit of a pain. Can facilitate better learning of CLI workflows.
- We will have access to the Nokia Garage. Can arrange to meet once-twice a week if necessary. Can loan a Pi, if needed. Likely better to meet in person, especially with access to equipment that makes things more standardized between team members.

- We will use Trello for project management.
- Thursday Zoom meetings with Amir (At 10:00), can also meet face to face if necessary.

## Ian's recommendation
Get together, teach each other, look at all the technologies and figure out where your strengths are, then assist each other in learning them. We should all come out of this with better understanding of the overall technologies, and the foundations of proper security practices.

## Ian's expectation
The technical side is not the issue. It's communication. "What I expect of you, and I'm really, really, serious, is that you get together, teach each other."

## General notes
Set up Github. Every time we meet, we should have something to show Ian. Doesn't matter if there's no UI. There should just be something new.

There are no stupid questions. Ask, when you're unsure. If you write on Discord "X does not work", this isn't helpful. Make an honest attempt to fix the issue, but also provide proper and thorough notes on your attempts when asking others, either on Discord or in person. To reiterate: Ask if you are uncertain of any aspect. It is only beneficial to work on your own learning. We're studying for a reason; we should strive to increase our understanding of these aspects.

## Nokia Garage and Intake procedure
Next meeting is on Monday the 18th, 9:00. Nokia, Espoo. Karamalmi. (Nokia coordinates: `60.22174, 24.7562`)

There's a reception desk. There will be a machine you type your name, host name (Ian Oliver, in this case). The receptionist will give you a badge. Ask her to give Ian a call, if he isn't already there. Always be nice to receptionists!

# Notes
Relevant technologies: `Golang`,  `Python`,  `Arduino`,  `MQTT`,   `JSON`,  `HTTP/REST`, and also take a look at `Influx`/`Grafana`.

## Important documentation and learning material
>From Ian:
>
>https://github.com/nokia/TPMCourse
>
>Go to the docs directory, also read the README :-)
>
>https://tpm2-software.github.io/
>
>https://tpm.dev
>
>https://www.youtube.com/watch?v=S6HWK8PF5MU

## Future meetings
Team meetings on Thursdays at 10:00, in Zoom. If necessary, we will also arrange for face-to-face meetings.

Meeting with Ian on Monday 18th, at 09:00
