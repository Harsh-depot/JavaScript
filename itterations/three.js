// for of
// ["", "", ""]
// [{}, {}, {}]

const arr = [1, 2, 3, 4, 5]

for (const num of arr) {
    // console.log(num);   
}

const greetings =  "hello world!"
for (const greet of greetings) {
    // console.log(`each char is ${greet}`);
}

// Maps    (unique values get as outputs, no repetitions)

const map = new Map()
map.set('IN', "India")
map.set('US', "United States of America")
map.set('UK', "United Kingdom")
map.set('IN', "India")

// console.log(map);

// for (const key of map) {
//     console.log(key);
// }

for (const [key, value] of map) {
    // console.log(key, ':-', value);
    
}

const myObject = {
    game1: 'NFS',
    game2: 'Spiderman',
    game3: 'COC'
}
 for (const [key, value] of myObject) {
    console.log(key, ':-', value);
    
 }

 //TypeError: myObject is not iterable