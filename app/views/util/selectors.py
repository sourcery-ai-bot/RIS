from copy import copy

from sqlalchemy import text

from app import db, models


def personChoicesForSelectField(persons=models.Person.query.all()):
    """
    Creates select field data for a list of persons.
    Formats the field as "ID - Last, First" to give a unique, readable entry.
    :param persons: List of persons to generate the data from.
        If not supplied, just queries the db for all persons.
    :return: Formatted list of choice tuples.
    """
    choices = []
    for person in persons:
        choices.append((person.person_id,
                        str(person.person_id) + " - " + ", ".join([person.last_name, person.first_name])))
    return choices


def diagnosesForSelectField():
    results = models.Record.query.group_by(models.Record.diagnosis).all()
    choices = [('all', 'All')]
    for res in results:
        choices.append((res.diagnosis, res.diagnosis))
    return choices


def selectPersonsWhoAreDoctors():
    """
    Helper method to select all persons who are doctors.
    :return: A list of persons who are doctors.
    """
    return db.session.query(models.Person).join(models.User).filter(models.User.user_class == 'd').all()


def selectPersonsWhoAreRadiologists():
    """
    Helper method to select all persons who are radiologists.
    :return: A list of persons who are radiologists.
    """
    return db.session.query(models.Person).join(models.User).filter(models.User.user_class == 'r').all()


def selectPersonsWhoArePatients():
    """
    Helper method to select all persons who are patients.
    :return: A list of persons who are patients.
    """
    return db.session.query(models.Person).join(models.User).filter(models.User.user_class == 'p').all()


def selectTableRowsUsingFormForDataAnalysis(form):
    """
    Builds an sql query from form parameters, executes it, and returns the results as a list.
    Used for Data Analysis Module.
    :param form: Form containing user selected dimensions to aggregate data by.
    :return: List of rows returned by the query. First row is table header.
    """
    selectFields = []
    tableHeader = []

    # SQL to create year, month, day fields
    year = "year(test_date) as year"
    month = "month(test_date) as month"
    day = "day(test_date) as day"

    # Populate selectFields and groupByClause from form
    if form.patient.data:
        selectFields.append("patient_id")
    if form.test_type.data:
        selectFields.append("test_type")

    if form.test_date.data:
        # Copy what has been picked so far
        tableHeader = copy(selectFields)
        # just year
        if form.test_date.data == "year":
            selectFields.append(year)
            tableHeader.append("year")
        # year and month
        if form.test_date.data == "month":
            selectFields.append(year)
            selectFields.append(month)
            tableHeader.append("year")
            tableHeader.append("month")
        # year and month and day
        if form.test_date.data == "day":
            selectFields.append(year)
            selectFields.append(month)
            selectFields.append(day)
            tableHeader.append("year")
            tableHeader.append("month")
            tableHeader.append("day")

    # Format the results for the SQL query
    if selectFields:
        selectFields = ",".join(selectFields) + ","
        groupByClause = "group by " + ",".join(tableHeader)
    else:
        selectFields = ""
        groupByClause = ""

    # Plug in the selectFields and groupByClause to the query
    query = """
        SELECT {selectFields} count(*) as num_images
        from radiology_record r join pacs_images p on r.record_id = p.record_id
        {groupByClause};
        """.format(selectFields=selectFields, groupByClause=groupByClause)

    # debug
    print(text(query))

    # execute
    results = db.engine.execute(text(query))

    # need to reformat as list of rows with a header
    tableHeader.append("num_images")
    resultsList = [tableHeader]
    resultsList += list(results)

    return resultsList


def selectPatientsUsingFormForReportGenerator(form):
    """
    Creates a list of patients with the selected diagnosis for the date range specified.
    Used by the Report Generator.
    :param form: Form containing the selected options.
    :return: List of rows returned by the query. First row is table header.
    """
    query = db.session.query(models.Person).join(models.Person.record_patient).group_by(models.Record.diagnosis)\
        .order_by(models.Record.test_date)

    # filter by diagnosis if not 'all'
    if form.diagnosis.data != 'all':
        query = query.filter(models.Record.diagnosis == form.diagnosis.data)

    # filter by date range if specified
    if form.start_date.data:
        query = query.filter(form.start_date.data <= models.Record.test_date)
    if form.end_date.data:
        query = query.filter(form.end_date.data >= models.Record.test_date)

    # header row
    resultsList = [["ID", "Last Name", "First Name", "Phone", "Diagnosis Date"]]

    # get the results as tuples rather than Person objects (closer to what we want)
    results = query.values(models.Person.person_id,
                           models.Person.last_name,
                           models.Person.first_name,
                           models.Person.phone,
                           models.Record.test_date)
    resultsList += list(results)
    return resultsList
