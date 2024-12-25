// Get the values from the URL query parameters
var queryString = window.location.search;
var urlParams = new URLSearchParams(queryString);
var nameOp = urlParams.get("name_op");
var requiredAmount = urlParams.get("required_amount");

// Update the elements on the page
$("span[t-esc='description']").text(nameOp);
$("span[t-esc='required_payment']").text(requiredAmount);
