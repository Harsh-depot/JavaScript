let score = "33"
//console.log(typeof score);
//console.log(typeof (score));

let score1 = 33
let valueInNumber = Number(score1)
//console.log(typeof valueInNumber);
//console.log(valueInNumber);

let score2 = "33abc"
let valueInNumber1 = Number(score2)
//console.log(typeof valueInNumber1);
//console.log(valueInNumber1);

let score3 = null
let valueInNumber2 = Number(score3)
//console.log(typeof valueInNumber2);
//console.log(valueInNumber2);

let score4 = undefined
let valueInNumber3 = Number(score4)
//console.log(typeof valueInNumber3);
//console.log(valueInNumber3);

// "33" => 33
// "33abc" => NaN
// null => 0
// undefined => NaN
// " " => 0
// true => 1
// false => 0

let isLoggedIn = 1
let booleanIsLoggedIn = Boolean(isLoggedIn)
//console.log(booleanIsLoggedIn);
//console.log(typeof booleanIsLoggedIn);

let isLoggedIn1 = ""
let booleanIsLoggedIn1 = Boolean(isLoggedIn1)
//console.log(booleanIsLoggedIn1);
//console.log(typeof booleanIsLoggedIn1);

let isLoggedIn2 = "harsh"
let booleanIsLoggedIn2 = Boolean(isLoggedIn2)
//console.log(booleanIsLoggedIn2);
//console.log(typeof booleanIsLoggedIn2);

// 1 => true
// 0 => false
// "" => false
// "harsh" => true

let someNumber = 33
let stringNumber = String(someNumber)
//console.log(stringNumber);
//console.log(typeof stringNumber);

// 33 => "33", string

//****************************Operations*********************/

// console.log(2 + 3);
// console.log(2-3);
// console.log(2*3);
// console.log(2/3);
// console.log(2**3);
// console.log(2%3);

let str1 = "Hello"
let str2 = "World"
let str3 = str1 + " " + str2
// console.log(str3);

// console.log(2 + "3");
// console.log("2" + 3);
// console.log((2 + 3) + "4");
// console.log("2" + (3 + 4));

// console.log(+true);
// console.log(+"");

let gameCounter = 100

// console.log(gameCounter);
// console.log(++gameCounter); prefix increment
// console.log(gameCounter++); postfix increment
