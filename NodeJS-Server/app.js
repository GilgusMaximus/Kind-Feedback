const http = require('http');
const fs = require('fs');
const express = require('express');
const path = require('path')
const bodyParser = require('body-parser');
const childP = require('child_process');

//setup
let app = express();
app.set('view engine', 'ejs');
app.use(express.static(__dirname + '/public'));
app.use(bodyParser.urlencoded({ extended: false }));
app.use(bodyParser.json());
var counter = 0;


let requestCurrentlyProcessed = true;
let lock = false;
let requested = false;

//start server
app.listen(8080);
console.log("Server started. Listening on 8080");




app.post('/submission', function(req, res) {
  res.render("submitted");
  console.log(req.body);
  let jsObject = {};
  jsObject.type = 1;
  jsObject.github_id = req.body.id;
  jsObject.supervisor_email = req.body.mail;
  fs.writeFileSync("../userDetails.json", JSON.stringify(jsObject));
  res.end();
});

//home page
app.get('/', function(req, res) {
  res.render("questionaire");
  var subprocess = childP.spawnSync('python', [
    "-u",
    path.join("../pr_parser", 'pr_parser.py')]);
  res.end();
});
