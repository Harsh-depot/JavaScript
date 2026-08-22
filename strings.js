const name = "harsh";
const repoCount = 10;

// console.log(name + repoCount); //harsh10

// console.log(`My name is ${name} and I have ${repoCount} repos`); //My name is harsh and I have 10 repos

const gameName = new String('harshvardhan-hvr');

console.log(gameName[5]);
console.log(gameName.__proto__);

console.log(gameName.length);
console.log(gameName.toUpperCase());

console.log(gameName.charAt(3));
console.log(gameName.indexOf('l'));

const newString = gameName.slice(0, 4);
console.log(newString);

const newString2 = gameName.substring(0, 4);
console.log(newString2);

const newString3 = gameName.slice(2, -1); //slice(startIndex, endIndex) //harshvardhan-hvr
console.log(newString3);