library(feather)
library(dplyr)
library(ggplot2)
library(tidyr)
library(lubridate)
library(purrr)
library(shiny)
library(RColorBrewer)

speed <- read_feather("data/Rechts_Speed_2011.feather")

names(speed) <- as.character(seq_along(speed))

ori <- as.POSIXct("2011-01-01 00:00:00", tz = "CET")
speed$time    <- as.POSIXct(seq(0, 60 * (nrow(speed) - 1), by = 60) , origin = ori)
speed$date    <- as.Date(speed$time, tz = "CET")
speed$min     <- factor(lubridate::minute(speed$time))
speed$hour    <- factor(lubridate::hour(speed$time))
speed$day     <- factor(lubridate::day(speed$time))
speed$wday    <- factor(lubridate::wday(speed$time))
speed$month   <- factor(lubridate::month(speed$time))

wd_lookup <- data_frame(num = 1:7,
                        day = c("Monday", "Tuesday", "Wednesday", 
                                "Thursday", "Friday", "Saturday", "Sunday"))
fr_lookup <- data_frame(num = list(0:59, seq(0, 55, by = 5), 
                                   seq(0, 45, 15), c(0, 30), 0),
                        choices = c("Every minute", "Every 5 minutes", 
                                    "Every 15 minutes", "Every 30 minutes", 
                                    "Every hour"))

colours <- colorRampPalette(brewer.pal(8,"Dark2"))(8)



ui <- fluidPage(
  sidebarLayout(
    sidebarPanel(
      h2("SELECT DATA"),
      p("Note: graphs will appear AFTER you select data!"),
      p("The data you are about to subset is A13 hectometer location data from 2011 supplied by
        Rotterdam Open Data. The data is the speed (km/hr) measured every minute at every 
        hectometer along the A13 in 2011. It's not Big data, but it's rather large. You can subset 
        days of the week, dates from and till (both inclusive), hours of the day, and numberdata 
        points per hour. The data ONLY subsets when you hit the 'Select' button."),
      checkboxGroupInput("weekday", "Weekdays", 
                         choices = c("Monday", "Tuesday", "Wednesday", 
                                     "Thursday", "Friday", "Saturday", "Sunday"),
                         selected = c("Thursday")),
      dateInput("date_from", "From", 
                value = as.Date("2011-09-01"), 
                min = as.Date("2011-01-01"),
                max = as.Date("2011-12-31")),
      dateInput("date_till", "Till", 
                value = as.Date("2011-09-07"), 
                min = as.Date("2011-01-01"),
                max = as.Date("2011-12-31")),
      sliderInput("time", "Hours of the day", 
                  min = 0, max = 23, value = c(17, 18)),
      radioButtons("freq", "Data Frequency", 
                   choices = c("Every minute", "Every 5 minutes", "Every 15 minutes", 
                               "Every 30 minutes", "Every hour"),
                   selected = "Every minute"),
      actionButton("select", "Select")
    ),
    
    mainPanel(
      h2("SEE THE PLOTS"),
      p("Graphs and a slider will appear here, after you select data. All three plots have a 
        common x-axis. The x-axis shows hectometers from 0 (at A4) to around 150 (near 
        Kleinpolderplein). The four vertical grey lines indicate the four junctions the A13 has."),
      p("The first plot appearing under here will show the average speed across whole A13. From the 
        selected data it shows the average speed of one particular minute averaged ovr the selected 
        days. Use the slider to slide over the remainder of your selected time.
        Example: if you chose Thursdays in April between 15-18 hour (time) every minute. Then the 
        slider lets you go from 15:00 till 18:59 passed every minute, and the plot shows you the 
        average speed at that minute for all Thursdays in April."),
      p("The plot is informative (and fun) because it allows you to see traffic jams appear and 
        crawl backwards as new cars join the back of a traffic jam and the front dissappears. Press
        the little play button in the slider for the animation. (Select a single day for nicest results)"),
      uiOutput("time_lapse_slider"),
      p("Current time in the plot:"),
      textOutput("time_text"),
      plotOutput("time_lapse"),
      p("The next two plots comes together. The last plot is similar to plot above, but averaged over
        each hour. You don't get to see the time lapse affect but it is a great summary of where the 
        traffic jams are most of the time. It is also a good compliment to the flux plot."),
      p("This plot shows the change in speed from one minute compared to the previous minute 
        at the same location (for each location). It calculated the absolute value of this difference 
        (slowing down is negative, speeding up is positive) and calculated the average. Now we have a 
        ‘flux’ number for each location on the road. Low values means constant flow of traffic, high
        values have a lot of slowing down and speeding up. Which is a sign of creating many traffic 
        jams."),
      plotOutput(outputId = "plot_flux_avg"),
      plotOutput(outputId = "plot_speed_avg")
      # plotOutput(outputId = "plot_flux_all")
    )
  )
)


server <- function(input, output) {

  select <- eventReactive(input$select, {
    
    df <- input$date_from
    dt <- input$date_till
    wd <- wd_lookup$num[wd_lookup$day %in% input$weekday]
    ti <- if(length(input$time) == 2) {
      input$time[1]:input$time[2]
    } else input$time
    fr <- fr_lookup$num[fr_lookup$choices == input$freq][[1]]
    
    list(df = df, dt = dt, wd = wd, ti = ti, fr = fr)
  })
    
  data <- eventReactive(select(), {
    df <- select()$df
    dt <- select()$dt
    wd <- select()$wd
    ti <- select()$ti
    fr <- select()$fr
    
    speed %>%
      filter(date >= df, date <= dt) %>% 
      filter(wday %in% wd) %>%
      filter(hour %in% ti) %>%
      filter(min %in% fr) %>%
      gather("dis", "speed", 1:143) %>%
      mutate(dis = as.integer(dis),
             hm  = as.factor(dis))
  })
  
  
  time_lapse_vector <- eventReactive(select(), {
    as.vector(t(outer(formatC(select()$ti, width = 2, flag = "0"), 
                      formatC(select()$fr, width = 2, flag = "0"), 
                      paste, sep = ":")))
  })
  
  output$time_lapse_slider <- renderUI({
    sliderInput("time_lapse", "Time Lapse Slider", 
                min = 1,
                max = length(time_lapse_vector()),
                value = 1,
                step = 1,
                animate = TRUE)
  })
  
  output$time_text <- renderText({
    time_lapse_vector()[input$time_lapse]
  })
  
  time_lapse_data <- eventReactive(data(), {
    data() %>% 
      group_by(dis, hour, min) %>% 
      summarise(speed = mean(speed))
  })
  
  output$time_lapse <- renderPlot({
    hh <- as.numeric(substr(time_lapse_vector()[input$time_lapse],1,2))
    mm <- as.numeric(substr(time_lapse_vector()[input$time_lapse],4,5))
    time_lapse_data() %>% 
      filter(hour == hh, min == mm) %>% 
      ggplot(aes(x = dis, y = speed)) +
        geom_point() +
        geom_vline(xintercept = c(19, 41, 60, 115), color = "darkgrey", linetype = 2) +
        labs(x = "Complete A13 by hectometer", y = "Average speed") +
        coord_cartesian(ylim = c(0, 120))
  })
  
  flux_avg <- eventReactive(data(), {
    data() %>% 
      group_by(hm, hour) %>% 
      summarise(diff  = mean(abs(speed[2:n()] - speed[1:(n()-1)])),
                speed = mean(speed[2:n()])) %>% 
      mutate(hm_num = as.numeric(hm))
  })
  
  output$plot_flux_avg <- renderPlot({ 
    ifelse(length(select()$fr > 1), fr <- select()$fr[2], fr <- 60)
    ylabs = paste0("Average fluctuation in speed per ", fr, " minute(s).")
    ggplot(flux_avg(), aes(x = hm_num, y = diff, col = hour)) +
      geom_line() + 
      labs(x = "Complete A13 by hectometer", y = ylabs) +
      geom_vline(xintercept = c(19, 41, 60, 115), color = "darkgrey", linetype = 2) +
      geom_text(aes(x = 19, label = "Brassenkade", y = 3), colour="darkgrey", angle =  90, vjust = 1.2) + 
      geom_text(aes(x = 41, label = "Oostporweg", y = 3), colour="darkgrey", angle = 90, vjust = 1.2) + 
      geom_text(aes(x = 60, label = "N470", y = 3), colour="darkgrey", angle = 90, vjust = 1.2) + 
      geom_text(aes(x = 115, label = "N209", y = 3), colour="darkgrey", angle = 90, vjust = 1.2)
  })
  
  output$plot_speed_avg <- renderPlot({ 
    
    ggplot(flux_avg(), aes(x = hm_num, y = speed, col = hour)) +
      geom_line() + 
      labs(x = "Complete A13 by hectometer", y = "Average speed") +
      geom_vline(xintercept = c(19, 41, 60, 115), color = "darkgrey", linetype = 2) +
      geom_text(aes(x = 19, label = "Brassenkade", y = 50), colour="darkgrey", angle =  90, vjust = 1.2) + 
      geom_text(aes(x = 41, label = "Oostporweg", y = 50), colour="darkgrey", angle = 90, vjust = 1.2) + 
      geom_text(aes(x = 60, label = "N470", y = 50), colour="darkgrey", angle = 90, vjust = 1.2) + 
      geom_text(aes(x = 115, label = "N209", y = 50), colour="darkgrey", angle = 90, vjust = 1.2)
  })
  
  
}



shinyApp(ui = ui, server = server)
