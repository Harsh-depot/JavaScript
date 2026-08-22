const accountId = 54321
let accountEmail = "xyz@gmail.com"
var accountPassword = "12345"
let accountCountry = "India"

accountEmail = "user@gmail.com"
accountPassword = "67890"
accountCountry = "USA"


/*
prefer not to use var, because of issues in block scope or functional scope 
*/
//accountId = 12

console.log(accountId);
console.table([accountId, accountEmail, accountPassword, accountCountry]);